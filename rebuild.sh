#!/bin/bash
# ============================================================
# AutoBox Docker 재빌드 스크립트
# 사용법: ./rebuild.sh [frontend|backend|all]
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/backend"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 프론트엔드 재빌드
rebuild_frontend() {
    log_info "프론트엔드 재빌드 시작..."
    
    # 기존 컨테이너 중지 및 삭제
    docker stop autobox-frontend 2>/dev/null || true
    docker rm autobox-frontend 2>/dev/null || true
    
    # 이미지 재빌드 (캐시 없이)
    log_info "Docker 이미지 빌드 중..."
    docker build --no-cache -t backend-frontend "$FRONTEND_DIR"
    
    # 컨테이너 실행
    log_info "컨테이너 시작 중..."
    docker run -d \
        --name autobox-frontend \
        --network autobox-network \
        -p 8081:80 \
        backend-frontend
    
    log_success "프론트엔드 재빌드 완료!"
}

# 백엔드 재빌드
rebuild_backend() {
    log_info "백엔드 재빌드 시작..."
    
    # 기존 컨테이너 중지 및 삭제
    docker stop autobox-backend 2>/dev/null || true
    docker rm autobox-backend 2>/dev/null || true
    
    # 이미지 재빌드 (캐시 없이)
    log_info "Docker 이미지 빌드 중..."
    docker build --no-cache -t backend-backend "$BACKEND_DIR"
    
    # 컨테이너 실행
    log_info "컨테이너 시작 중..."
    docker run -d \
        --name autobox-backend \
        --network autobox-network \
        -p 8080:8000 \
        -v "$BACKEND_DIR/data:/app/data" \
        --env-file "$BACKEND_DIR/.env" \
        backend-backend
    
    log_success "백엔드 재빌드 완료!"
}

# 사용하지 않는 이미지 정리
cleanup_images() {
    log_info "사용하지 않는 Docker 이미지 정리 중..."
    docker image prune -f
    log_success "정리 완료!"
}

# 상태 확인
show_status() {
    echo ""
    log_info "현재 컨테이너 상태:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "autobox|NAMES"
}

# 메인 로직
case "${1:-all}" in
    frontend|fe|f)
        rebuild_frontend
        cleanup_images
        show_status
        ;;
    backend|be|b)
        rebuild_backend
        cleanup_images
        show_status
        ;;
    all|a)
        rebuild_backend
        rebuild_frontend
        cleanup_images
        show_status
        ;;
    status|s)
        show_status
        ;;
    clean|c)
        cleanup_images
        ;;
    *)
        echo "사용법: $0 [frontend|backend|all|status|clean]"
        echo ""
        echo "옵션:"
        echo "  frontend, fe, f  - 프론트엔드만 재빌드"
        echo "  backend, be, b   - 백엔드만 재빌드"
        echo "  all, a           - 전체 재빌드 (기본값)"
        echo "  status, s        - 컨테이너 상태 확인"
        echo "  clean, c         - 사용하지 않는 이미지 정리"
        exit 1
        ;;
esac

echo ""
log_success "완료!"
