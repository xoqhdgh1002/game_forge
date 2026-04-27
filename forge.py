#!/usr/bin/env python3
"""
Game Forge — AI 에이전트 게임 개발 팀
아이디어 한 줄 → 즉시 실행 가능한 HTML5 게임

사용법:
  python3 forge.py "무한 점프 게임, 장애물 피하기"
  python3 forge.py "아이디어" --style retro --deploy
  python3 forge.py "탑뷰 RPG" --assets
  python3 forge.py "탑뷰 RPG" --assets --assets-url "https://itch.io/game-assets/free/tag-rpg"
"""
import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from orchestrator import orchestrate


def _slug(idea: str) -> str:
    s = idea.lower()
    s = re.sub(r"[^a-z0-9가-힣\s]", "", s)
    s = re.sub(r"[가-힣]", "", s).strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        s = "game"
    ts = datetime.now().strftime("%m%d%H%M")
    return f"gf-{s[:18]}-{ts}"[:28].rstrip("-")


def deploy_to_cloudflare(game_path: Path, project_name: str) -> str | None:
    deploy_script = Path(__file__).parent / "deploy.sh"
    if not deploy_script.exists():
        print("   ⚠️  deploy.sh 없음 — 배포 건너뜀")
        return None
    try:
        result = subprocess.run(
            ["bash", str(deploy_script), str(game_path), project_name],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            return f"https://{project_name}.pages.dev"
        print(f"   ❌ 배포 실패:\n{(result.stdout + result.stderr)[-500:]}")
        return None
    except Exception as e:
        print(f"   ❌ 배포 오류: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="AI 에이전트 게임 개발 팀 — 아이디어 → HTML5 게임",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python3 forge.py "슈팅 게임"
  python3 forge.py "우주선 슈팅" --style neon --deploy
  python3 forge.py "탑뷰 RPG" --assets
  python3 forge.py "블록 퍼즐" --skip-qa --deploy
        """,
    )
    parser.add_argument("idea", help="게임 아이디어 (한 줄)")
    parser.add_argument("--style", default="pixel",
                        choices=["pixel", "retro", "modern", "minimal", "neon"])
    parser.add_argument("--engine", default="vanilla", choices=["vanilla", "phaser"])
    parser.add_argument("--skip-qa", action="store_true")
    parser.add_argument("--deploy", action="store_true",
                        help="Cloudflare Pages 배포 → 링크 발급")
    parser.add_argument("--assets", action="store_true",
                        help="itch.io 에셋 자동 수집 (Asset Collector 활성화)")
    parser.add_argument("--assets-url",
                        default="https://itch.io/game-assets/free/tag-2d/tag-pixel-art")
    parser.add_argument("--max-retries", type=int, default=2,
                        help="QA 크리티컬 버그 발생 시 Developer 재시도 최대 횟수 (기본 2)")

    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(__file__).parent / "output" / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🎮 Game Forge 시작")
    print(f"   아이디어: {args.idea}")
    print(f"   스타일: {args.style}  엔진: {args.engine}  "
          f"에셋: {'on' if args.assets else 'off'}  "
          f"QA: {'off' if args.skip_qa else 'on'}  "
          f"재시도: {args.max_retries}회  "
          f"배포: {'on' if args.deploy else 'off'}")
    print(f"   출력: {out_dir}")
    print(f"   → Orchestrator Agent가 파이프라인을 자율 지휘합니다\n")

    success = orchestrate(
        idea=args.idea,
        style=args.style,
        engine=args.engine,
        output_dir=str(out_dir),
        use_assets=args.assets,
        itchio_url=args.assets_url,
        skip_qa=args.skip_qa,
        max_retries=args.max_retries,
    )

    game_path = out_dir / "game.html"

    if not success:
        print(f"\n❌ 게임 생성 실패. 로그 확인: {out_dir}")
        sys.exit(1)

    # 배포
    url = None
    if args.deploy:
        print(f"\n🌐 Cloudflare Pages 배포 중...")
        project_name = _slug(args.idea)
        url = deploy_to_cloudflare(game_path, project_name)

    print(f"\n{'='*60}")
    print(f"✅ 게임 생성 완료!")
    print(f"   로컬 파일: {game_path}")
    if url:
        print(f"   🌐 링크: {url}")
    else:
        print(f"   열기: open '{game_path}'")
        if not args.deploy:
            print(f"   배포: ./run.sh \"{args.idea}\" --deploy")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
