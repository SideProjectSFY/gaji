COMPOSE_DEV		:= docker-compose.dev.yml
COMPOSE_PROD	:= docker-compose.prod.yml

# 환경 변수 파일 경로
ENV_DEV_FILE		:= .env
ENV_PROD_FILE		:= .env.prod

# Docker 빌드 설정 (타임아웃 증가)
export DOCKER_BUILDKIT=1
export COMPOSE_HTTP_TIMEOUT=600
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_CLIENT_TIMEOUT=600
export BUILDKIT_STEP_LOG_MAX_SIZE=10485760
export BUILDKIT_PROGRESS=plain

all: dev

# dev: 재시도 로직 추가
dev:
	@echo "🚀 Starting development build (with retry logic)..."
	@for i in 1 2 3; do \
		echo "📦 Build attempt $$i/3..."; \
		if docker compose --env-file $(ENV_DEV_FILE) -f $(COMPOSE_DEV) up --build -d; then \
			echo "✅ Build successful!"; \
			exit 0; \
		else \
			echo "❌ Build attempt $$i failed"; \
			if [ $$i -lt 3 ]; then \
				echo "⏳ Waiting 10 seconds before retry..."; \
				sleep 10; \
			fi; \
		fi; \
	done; \
	echo "💥 All build attempts failed"; \
	exit 1

# dev-pull: Base 이미지를 미리 pull한 후 빌드 (타임아웃 방지)
dev-pull:
	@echo "📥 Pre-pulling base images to avoid timeout..."
	@docker pull eclipse-temurin:17-jdk || echo "Warning: Failed to pull eclipse-temurin"
	@docker pull python:3.11-slim || echo "Warning: Failed to pull python"
	@docker pull python:3.11-alpine || echo "Warning: Failed to pull python-alpine"
	@echo "🚀 Starting development build..."
	docker compose --env-file $(ENV_DEV_FILE) -f $(COMPOSE_DEV) up --build -d

# prod: 재시도 로직 추가 (최대 3회 시도) + DB 초기화
prod:
	@echo "🚀 Starting production deployment..."
	@echo "🗄️  Step 1: Cleaning up old containers and volumes..."
	@docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) down 2>/dev/null || true
	@docker volume rm gaji_postgres-data 2>/dev/null || echo "No postgres volume to remove"
	@echo ""
	@echo "📦 Step 2: Starting PostgreSQL first..."
	@docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) up -d postgres
	@echo "⏳ Waiting for PostgreSQL to initialize (15 seconds)..."
	@sleep 15
	@echo ""
	@echo "🔍 Step 3: Verifying database creation..."
	@docker exec gaji-postgres psql -U gaji_user -d gaji_db -c "SELECT version();" || \
		(echo "❌ Database verification failed" && exit 1)
	@echo "✅ Database ready!"
	@echo ""
	@echo "🚀 Step 4: Building and starting all services (with retry logic)..."
	@for i in 1 2 3; do \
		echo "📦 Build attempt $$i/3..."; \
		if docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) up --build -d; then \
			echo "✅ Deployment successful!"; \
			exit 0; \
		else \
			echo "❌ Build attempt $$i failed"; \
			if [ $$i -lt 3 ]; then \
				echo "⏳ Waiting 30 seconds before retry..."; \
				sleep 30; \
			fi; \
		fi; \
	done; \
	echo "💥 All build attempts failed"; \
	exit 1

# prod-fast: 빌드 없이 기존 이미지로 시작 (빌드 타임아웃 회피)
prod-fast:
	@echo "⚡ Starting production with existing images (no build)..."
	docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) up -d

# prod-pull: Base 이미지를 미리 pull한 후 빌드 (타임아웃 방지)
prod-pull:
	@echo "📥 Pre-pulling base images to avoid timeout..."
	@echo "⏳ Pulling eclipse-temurin:17-jdk..."
	@docker pull eclipse-temurin:17-jdk --platform linux/amd64 || echo "⚠️  Warning: Failed to pull eclipse-temurin:17-jdk"
	@echo "⏳ Pulling eclipse-temurin:17-jre..."
	@docker pull eclipse-temurin:17-jre --platform linux/amd64 || echo "⚠️  Warning: Failed to pull eclipse-temurin:17-jre"
	@echo "⏳ Pulling python:3.11-slim..."
	@docker pull python:3.11-slim --platform linux/amd64 || echo "⚠️  Warning: Failed to pull python:3.11-slim"
	@echo "⏳ Pulling python:3.11-alpine..."
	@docker pull python:3.11-alpine --platform linux/amd64 || echo "⚠️  Warning: Failed to pull python:3.11-alpine"
	@echo "⏳ Pulling ghcr.io/astral-sh/uv:latest..."
	@docker pull ghcr.io/astral-sh/uv:latest --platform linux/amd64 || echo "⚠️  Warning: Failed to pull uv"
	@echo "✅ Base images pulled successfully!"
	@echo "🚀 Starting production build..."
	docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) up --build -d

# prod-safe: 안전한 프로덕션 빌드 (이미지를 먼저 pull한 후 개별 서비스 빌드)
prod-safe:
	@echo "🔒 Starting safe production deployment..."
	@echo "🗄️  Step 1: Cleaning up old containers and volumes..."
	@docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) down 2>/dev/null || true
	@docker volume rm gaji_postgres-data 2>/dev/null || echo "No postgres volume to remove"
	@echo ""
	@echo "📥 Step 2: Pre-pulling all base images..."
	@$(MAKE) -s prod-pull-only
	@echo ""
	@echo "📦 Step 3: Starting PostgreSQL first..."
	@docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) up -d postgres
	@echo "⏳ Waiting for PostgreSQL to initialize (15 seconds)..."
	@sleep 15
	@echo ""
	@echo "🔍 Step 4: Verifying database creation..."
	@docker exec gaji-postgres psql -U gaji_user -d gaji_db -c "SELECT version();" || \
		(echo "❌ Database verification failed" && exit 1)
	@echo "✅ Database ready!"
	@echo ""
	@echo "🏗️  Step 5: Building services one by one..."
	@docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) build --no-cache backend || echo "⚠️  Backend build failed"
	@docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) build --no-cache ai-service || echo "⚠️  AI Service build failed"
	@docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) build --no-cache monitor || echo "⚠️  Monitor build failed"
	@echo ""
	@echo "🚀 Step 6: Starting all services..."
	@docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) up -d
	@echo "✅ Safe production deployment completed!"

# prod-pull-only: Base 이미지만 pull (빌드는 하지 않음)
prod-pull-only:
	@echo "📥 Pre-pulling base images..."
	@echo "Pulling eclipse-temurin:17-jdk..."
	@timeout 120 docker pull eclipse-temurin:17-jdk --platform linux/amd64 2>&1 || echo "⚠️  Failed: eclipse-temurin:17-jdk"
	@sleep 2
	@echo "Pulling eclipse-temurin:17-jre..."
	@timeout 120 docker pull eclipse-temurin:17-jre --platform linux/amd64 2>&1 || echo "⚠️  Failed: eclipse-temurin:17-jre"
	@sleep 2
	@echo "Pulling python:3.11-slim..."
	@timeout 120 docker pull python:3.11-slim --platform linux/amd64 2>&1 || echo "⚠️  Failed: python:3.11-slim"
	@sleep 2
	@echo "Pulling python:3.11-alpine..."
	@timeout 120 docker pull python:3.11-alpine --platform linux/amd64 2>&1 || echo "⚠️  Failed: python:3.11-alpine"
	@sleep 2
	@echo "Pulling ghcr.io/astral-sh/uv:latest..."
	@timeout 120 docker pull ghcr.io/astral-sh/uv:latest --platform linux/amd64 2>&1 || echo "⚠️  Failed: uv"
	@sleep 2
	@echo "Pulling chromadb/chroma:latest..."
	@timeout 120 docker pull chromadb/chroma:latest --platform linux/amd64 2>&1 || echo "⚠️  Failed: chromadb"
	@sleep 2
	@echo "Pulling postgres:15-alpine..."
	@timeout 120 docker pull postgres:15-alpine --platform linux/amd64 2>&1 || echo "⚠️  Failed: postgres"
	@sleep 2
	@echo "Pulling redis:7-alpine..."
	@timeout 120 docker pull redis:7-alpine --platform linux/amd64 2>&1 || echo "⚠️  Failed: redis"
	@sleep 2
	@echo "Pulling nginx:alpine..."
	@timeout 120 docker pull nginx:alpine --platform linux/amd64 2>&1 || echo "⚠️  Failed: nginx"
	@echo "✅ Image pull attempts completed!"


# diagnose: Docker 네트워크 진단
diagnose:
	@echo "🔍 Docker Network Diagnostics"
	@echo "=============================="
	@echo "\n1. Docker Info:"
	@docker info | grep -E "Registry|DNS|HTTP Proxy" || echo "No proxy configured"
	@echo "\n2. Testing Docker Hub connectivity:"
	@curl -I --max-time 10 https://registry-1.docker.io/v2/ || echo "❌ Cannot reach Docker Hub"
	@echo "\n3. Testing DNS resolution:"
	@nslookup registry-1.docker.io || echo "❌ DNS resolution failed"
	@echo "\n4. Current Docker images:"
	@docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}"
	@echo "\n5. Docker daemon status:"
	@docker version | grep -E "Version|API version" || echo "❌ Docker daemon issue"

clean:
	docker compose --env-file $(ENV_DEV_FILE) -f $(COMPOSE_DEV) down
	docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) down 2>/dev/null || true

fclean:
	docker compose --env-file $(ENV_DEV_FILE) -f $(COMPOSE_DEV) down --rmi all --volumes --remove-orphans
	docker compose --env-file $(ENV_PROD_FILE) -f $(COMPOSE_PROD) down --rmi all --volumes --remove-orphans 2>/dev/null || true
	docker system prune --all --volumes --force

re:
	make clean
	make dev


.PHONY: all dev dev-pull prod prod-fast prod-pull prod-safe prod-pull-only diagnose clean fclean re