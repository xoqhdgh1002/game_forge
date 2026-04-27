#!/usr/bin/env python3
"""
CLI 래퍼 — Modifier 에이전트 실행
사용법: python3 run_modifier.py <output_dir> "<changes>"
  <output_dir>/game.html 을 읽어 수정 후 덮어쓴다.
  <output_dir>/modify_report.md 생성
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.modifier import modify

out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
changes = sys.argv[2] if len(sys.argv) > 2 else ""

if not changes:
    print("ERROR: 수정 요청 없음", file=sys.stderr)
    sys.exit(1)

success = modify(str(out_dir), changes)

if not success:
    print("ERROR: 수정 실패", file=sys.stderr)
    sys.exit(1)

game_path = out_dir / "game.html"
print(f"OK: {game_path} ({game_path.stat().st_size // 1024}KB)")
