#!/usr/bin/env python3
"""
CLI 래퍼 — Developer 에이전트 실행
사용법: python3 run_developer.py <output_dir> [engine]
  <output_dir>/gdd.md + design.md (+ assets.json + sounds.json) 를 읽어
  <output_dir>/game.html 생성 후 exit 0
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.developer import develop

out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
engine  = sys.argv[2] if len(sys.argv) > 2 else "vanilla"

gdd_path    = out_dir / "gdd.md"
design_path = out_dir / "design.md"
assets_path = out_dir / "assets.json"
sounds_path = out_dir / "sounds.json"
game_path   = out_dir / "game.html"

if not gdd_path.exists():
    print(f"ERROR: {gdd_path} 없음", file=sys.stderr)
    sys.exit(1)
if not design_path.exists():
    print(f"ERROR: {design_path} 없음", file=sys.stderr)
    sys.exit(1)

gdd        = gdd_path.read_text(encoding="utf-8")
design_doc = design_path.read_text(encoding="utf-8")

assets_data: dict = {"assets": [], "fallback_to_canvas": True}
if assets_path.exists():
    try:
        assets_data = json.loads(assets_path.read_text(encoding="utf-8"))
    except Exception:
        pass

sounds_data: dict = {}
if sounds_path.exists():
    try:
        sounds_data = json.loads(sounds_path.read_text(encoding="utf-8"))
    except Exception:
        pass

result = develop(
    gdd, design_doc, str(game_path),
    engine=engine,
    assets_data=assets_data,
    sounds_data=sounds_data,
)
if not result:
    print("ERROR: Developer가 빈 결과를 반환했습니다.", file=sys.stderr)
    sys.exit(1)

print(f"OK: {game_path} ({len(result)}자, {game_path.stat().st_size // 1024}KB)")
