#!/usr/bin/env python3
"""
CLI 래퍼 — Asset Collector 에이전트 실행
사용법: python3 run_asset_collector.py <output_dir> [itchio_url]
  <output_dir>/design.md 를 읽어 <output_dir>/assets.json 생성 후 exit 0
  에셋 수집 실패 시에도 exit 0 (fallback_to_canvas: true 로 저장)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.asset_collector import collect

out_dir    = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
itchio_url = sys.argv[2] if len(sys.argv) > 2 else "https://itch.io/game-assets/free/tag-2d/tag-pixel-art"

design_path = out_dir / "design.md"
if not design_path.exists():
    print(f"ERROR: {design_path} 없음 — Designer를 먼저 실행하세요.", file=sys.stderr)
    sys.exit(1)

design_text = design_path.read_text(encoding="utf-8")
design_summary = design_text[:500]

assets_path = str(out_dir / "assets.json")
assets_data = collect(
    design_summary=design_summary,
    work_dir=str(out_dir),
    output_path=assets_path,
    itchio_url=itchio_url,
)

asset_count = len(assets_data.get("assets", []))
fallback    = assets_data.get("fallback_to_canvas", True)

if fallback:
    print(f"FALLBACK: 에셋 수집 실패 — Canvas 도형으로 대체 ({assets_path})")
else:
    print(f"OK: {assets_path} ({asset_count}개 에셋)")
