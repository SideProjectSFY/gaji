#!/bin/bash
set -e

echo "🔐 Extracting Caddy certificates for api.gaji.me..."

DOCKER_CONTAINER="gaji-caddy"
DOMAIN="api.gaji.me"
OUTPUT_DIR="./netlify-certs"

mkdir -p $OUTPUT_DIR

# 인증서 경로 (로그 기반)
CERT_PATH="/data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/$DOMAIN"

echo "📂 Certificate path: $CERT_PATH"
echo ""

# 파일 목록 확인
echo "📋 Files in certificate directory:"
docker exec $DOCKER_CONTAINER ls -la "$CERT_PATH" 2>/dev/null || {
    echo "❌ Certificate directory not found"
    echo "🔍 Searching for certificates..."
    docker exec $DOCKER_CONTAINER find /data/caddy/certificates -name "*.crt" -o -name "*.key"
    exit 1
}

echo ""

# 1. Certificate 추출
echo "🐳 Extracting certificate..."
docker cp "$DOCKER_CONTAINER:$CERT_PATH/$DOMAIN.crt" "$OUTPUT_DIR/certificate.pem"
echo "✅ Certificate: $OUTPUT_DIR/certificate.pem"

# 2. Private Key 추출
echo "🐳 Extracting private key..."
docker cp "$DOCKER_CONTAINER:$CERT_PATH/$DOMAIN.key" "$OUTPUT_DIR/private-key.pem"
echo "✅ Private key: $OUTPUT_DIR/private-key.pem"

echo ""

# 3. 인증서 정보 확인
echo "📄 Certificate details:"
openssl x509 -in "$OUTPUT_DIR/certificate.pem" -noout -text | grep -A 2 "Subject:"
openssl x509 -in "$OUTPUT_DIR/certificate.pem" -noout -text | grep -A 2 "Validity"

echo ""

# 4. 만료일 확인
EXPIRY=$(openssl x509 -in "$OUTPUT_DIR/certificate.pem" -noout -enddate | cut -d= -f2)
echo "📅 Certificate expires: $EXPIRY"

# 5. Netlify 업로드용 출력
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Copy these to Netlify:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "=== Certificate ==="
cat "$OUTPUT_DIR/certificate.pem"
echo ""
echo "=== Private Key ==="
cat "$OUTPUT_DIR/private-key.pem"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  After uploading to Netlify, DELETE these files:"
echo "   rm -rf $OUTPUT_DIR"