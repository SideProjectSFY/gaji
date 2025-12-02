COMPOSE_FILE		:= docker-compose.yml

# 환경 변수 파일 경로
ENV_DB_FILE			:= .env

all:
	DOCKER_BUILDKIT=1 docker compose -f $(COMPOSE_FILE) up --build -d

clean:
	docker compose -f $(COMPOSE_FILE) down

fclean:
	docker compose -f $(COMPOSE_FILE) down --rmi all --volumes --remove-orphans
	docker system prune --all --volumes --force

re:
	make clean
	make all


.PHONY: all clean fclean re
