"""
Modifier Agent v2 — 기존 game.html을 외과적으로 수정한다.

v2 개선: Write(전체 재작성) 대신 Edit(부분 수정)을 사용하도록 지시.
         작은 변경은 수십 줄만 교체하고 나머지는 건드리지 않는다.
"""
import asyncio
from pathlib import Path

from claude_agent_sdk import query as agent_query, ClaudeAgentOptions, ResultMessage

SYSTEM = """당신은 12년 경력의 시니어 HTML5 게임 개발자이자 외과적 코드 수정 전문가다.

─────────────────────────────────────────
■ 핵심 원칙: Edit 도구 우선
─────────────────────────────────────────
**반드시 Edit 도구로 수정한다. Write 도구는 금지.**

Edit 도구 사용법:
  - old_string: 수정할 코드 (고유하게 특정되는 충분한 컨텍스트 포함)
  - new_string: 바꿀 코드

예시 (속도 변경):
  Edit(
    file_path="game.html",
    old_string="const PLAYER_SPEED = 300;",
    new_string="const PLAYER_SPEED = 500; // 원본: 300"
  )

예시 (색상 변경):
  Edit(
    file_path="game.html",
    old_string="ctx.fillStyle = '#FF0000';",
    new_string="ctx.fillStyle = '#00FF00';"
  )

─────────────────────────────────────────
■ 작업 순서
─────────────────────────────────────────
1. Read 도구로 game.html 전체를 읽는다.
2. 수정이 필요한 코드 조각을 정확히 찾는다.
3. Edit 도구로 해당 부분만 교체한다 (여러 번 호출 가능).
4. Write 도구로 modify_report.md를 작성한다.
5. "✅ 수정 완료" 출력.

─────────────────────────────────────────
■ 수정 철학
─────────────────────────────────────────
- 요청한 것만 바꾼다. 나머지 코드는 절대 손대지 않는다.
- 수치 변경 시 원본 값을 주석으로 남긴다.
- 관련 상수가 여러 곳에 있으면 모두 찾아서 일관되게 수정한다.
- 기능 추가 시 기존 코드 구조(섹션 주석)를 따른다.

─────────────────────────────────────────
■ 절대 규칙
─────────────────────────────────────────
RULE-01: Write 도구로 game.html 전체를 덮어쓰는 것은 **절대 금지**.
RULE-02: 수정 후에도 게임이 완전히 실행 가능한 상태여야 한다.
RULE-03: modify_report.md에 변경 전→후를 명시한다.
RULE-04: 요청이 기술적으로 불가능하면 이유와 대안을 report에 기록한다.
"""


async def _run_modifier(output_path: str, report_path: str, changes: str) -> str:
    prompt = f"""아래 게임을 수정하라.

─────────────────────────────────────────
수정 요청
─────────────────────────────────────────
{changes}

─────────────────────────────────────────
파일 경로
─────────────────────────────────────────
게임 파일: {output_path}
수정 보고서: {report_path}

─────────────────────────────────────────
지시사항
─────────────────────────────────────────
1. Read 도구로 {output_path}를 읽는다.
2. 수정이 필요한 부분을 찾는다.
3. Edit 도구로 해당 부분만 수정한다 (Write 금지).
4. Write 도구로 {report_path}에 변경 보고서를 작성한다.
5. "✅ 수정 완료"를 출력한다.
"""

    result_text = ""
    async for msg in agent_query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Write"],
            disallowed_tools=["Bash", "computer"],
            system_prompt=SYSTEM,
            cwd=str(Path(output_path).parent),
        ),
    ):
        if isinstance(msg, ResultMessage):
            result_text = (msg.result or "").strip()
    return result_text


def modify(output_dir: str, changes: str) -> bool:
    out_path    = Path(output_dir)
    game_path   = out_path / "game.html"
    report_path = out_path / "modify_report.md"

    if not game_path.exists():
        print(f"ERROR: {game_path} 없음", flush=True)
        return False

    asyncio.run(_run_modifier(
        output_path=str(game_path),
        report_path=str(report_path),
        changes=changes,
    ))

    return game_path.exists() and game_path.stat().st_size > 500
