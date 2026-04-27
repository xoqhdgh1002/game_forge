#!/usr/bin/env python3
"""
CLI 래퍼 — Designer 에이전트 실행
사용법: python3 run_designer.py <output_dir>
  <output_dir>/gdd.md 를 읽어 <output_dir>/design.md 생성 후 exit 0
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.designer import design

out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
gdd_path = out_dir / "gdd.md"

if not gdd_path.exists():
    print(f"ERROR: {gdd_path} 없음 — Producer를 먼저 실행하세요.", file=sys.stderr)
    sys.exit(1)

gdd = gdd_path.read_text(encoding="utf-8")
result = design(gdd)
if not result:
    print("ERROR: Designer가 빈 결과를 반환했습니다.", file=sys.stderr)
    sys.exit(1)

(out_dir / "design.md").write_text(f"# 세부 설계\n\n{result}", encoding="utf-8")
print(f"OK: {out_dir}/design.md ({len(result)}자)")
