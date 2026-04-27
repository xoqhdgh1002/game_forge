#!/usr/bin/env python3
"""
CLI 래퍼 — Producer 에이전트 실행
사용법: python3 run_producer.py <idea> <style> <engine> <output_dir>
성공 시 <output_dir>/gdd.md 생성 후 exit 0
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.producer import produce

idea      = sys.argv[1]
style     = sys.argv[2] if len(sys.argv) > 2 else "pixel"
engine    = sys.argv[3] if len(sys.argv) > 3 else "vanilla"
out_dir   = Path(sys.argv[4]) if len(sys.argv) > 4 else Path(".")

result = produce(idea, style=style, engine=engine)
if not result:
    print("ERROR: Producer가 빈 결과를 반환했습니다.", file=sys.stderr)
    sys.exit(1)

out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "gdd.md").write_text(f"# GDD 초안\n\n{result}", encoding="utf-8")
print(f"OK: {out_dir}/gdd.md ({len(result)}자)")
