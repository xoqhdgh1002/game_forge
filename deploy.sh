#!/usr/bin/env bash
# Game Forge 전용 Cloudflare Pages 배포 스크립트
# 사용법: bash deploy.sh <html파일경로> <프로젝트명>
set -e

HTML_FILE="${1:-}"
PROJECT_NAME="${2:-gf-game}"

if [ -z "$HTML_FILE" ] || [ ! -f "$HTML_FILE" ]; then
    echo "❌ HTML 파일이 없습니다: $HTML_FILE"
    exit 1
fi

# Node v24 + wrangler 설정
export NVM_DIR="$HOME/.nvm"
source "$NVM_DIR/nvm.sh" 2>/dev/null
nvm use 24 2>/dev/null

WRANGLER=$(find ~/.nvm/versions/node/v24*/bin/wrangler 2>/dev/null | head -1)
if [ -z "$WRANGLER" ]; then
    echo "❌ wrangler를 찾을 수 없습니다"
    exit 1
fi

# 배포 디렉토리 준비
DEPLOY_DIR="$(mktemp -d)"
cp "$HTML_FILE" "$DEPLOY_DIR/index.html"

echo "🚀 배포 중: $PROJECT_NAME"

# 프로젝트 없으면 먼저 생성
"$WRANGLER" pages project create "$PROJECT_NAME" --production-branch main 2>/dev/null || true

# 배포 (git worktree 외부이므로 --commit-dirty=true)
OUTPUT=$("$WRANGLER" pages deploy "$DEPLOY_DIR" \
    --project-name "$PROJECT_NAME" \
    --branch main \
    --commit-dirty=true 2>&1)

echo "$OUTPUT"
rm -rf "$DEPLOY_DIR"

# 정규 URL (해시 prefix 없는 버전) 출력
CANONICAL="https://${PROJECT_NAME}.pages.dev"
echo ""
echo "✅ 배포 완료: $CANONICAL"
