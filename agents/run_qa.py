#!/usr/bin/env python3
"""
CLI 래퍼 — QA 에이전트 실행
사용법: python3 run_qa.py <output_dir>
  <output_dir>/game.html 을 검토하고 수정 후 <output_dir>/qa_report.md 저장
  exit 0: QA 통과 (크리티컬 없음)
  exit 2: 크리티컬 버그 발견 (재작업 필요)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.qa import review

out_dir   = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
game_path = out_dir / "game.html"

if not game_path.exists():
    print(f"ERROR: {game_path} 없음 — Developer를 먼저 실행하세요.", file=sys.stderr)
    sys.exit(1)

qa_report, fixed_html = review(str(game_path))

# 폴백: QA가 Write 도구로 직접 안 쓴 경우
if fixed_html:
    game_path.write_text(fixed_html, encoding="utf-8")

report_path = out_dir / "qa_report.md"
report_path.write_text(f"# QA 리포트\n\n{qa_report}", encoding="utf-8")

# 크리티컬 버그 여부 판단
has_critical = "🔴" in qa_report or "크리티컬" in qa_report.lower()

if has_critical:
    print(f"CRITICAL: 크리티컬 버그 발견 — {report_path}")
    sys.exit(2)
else:
    print(f"OK: QA 통과 — {report_path}")
    sys.exit(0)
