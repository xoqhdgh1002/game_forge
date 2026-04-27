"""
Modifier Agent — 기존 game.html을 읽고 수정 요청을 적용한다.

역할: 완성된 게임의 코드를 정밀하게 수정한다.
      처음부터 새로 짜는 게 아니라, 기존 코드 구조를 최대한 유지하면서
      요청된 변경 사항만 외과적으로 적용한다.

출력: <output_dir>/game.html (수정됨)
      <output_dir>/modify_report.md (변경 내역)
"""
import asyncio
import re
from pathlib import Path

from claude_agent_sdk import query as agent_query, ClaudeAgentOptions, ResultMessage

SYSTEM = """당신은 12년 경력의 시니어 HTML5 게임 개발자이자 코드 수정 전문가다.
기존 게임 코드를 받아 요청된 변경 사항을 정밀하게 적용하는 것이 지금의 임무다.

─────────────────────────────────────────
■ 수정 철학
─────────────────────────────────────────
1. 최소 변경 원칙
   - 요청한 것만 바꾼다. 건드리지 않아도 되는 코드는 절대 손대지 않는다.
   - "이왕 여기 왔으니 이것도 고치자"는 없다.
   - 변수명 변경, 코드 재구조화, 스타일 통일 같은 사이드 작업 금지.

2. 코드 이해 우선
   - 수정 전 반드시 전체 코드를 읽고 구조를 파악한다.
   - 변수가 어디서 선언되고 어디서 사용되는지 추적한다.
   - 충돌 가능성(예: 속도 상수가 여러 곳에서 참조됨)을 미리 파악한다.

3. 수치 변경 시
   - 원본 값을 주석으로 남긴다. 예: `const SPEED = 600; // 원본: 300`
   - 관련된 모든 상수를 같이 조정한다. (속도 올리면 게임 난이도도 맞게 조정)

4. 기능 추가 시
   - 기존 코드의 섹션 구조(SECTION 주석)를 따른다.
   - 새 함수는 기존 함수 다음에 추가한다.
   - 새 변수는 기존 변수 선언부에 추가한다.

5. 기능 제거 시
   - 완전히 삭제하되, 관련 참조(호출부, 이벤트 리스너 등)도 함께 제거한다.
   - 주석만 남기는 방식은 사용하지 않는다.

─────────────────────────────────────────
■ 수정 가능한 항목 예시
─────────────────────────────────────────
속도·크기:
  - 플레이어 속도, 적 속도, 점프력, 중력
  - 오브젝트 크기 (플레이어, 적, 총알, 아이템)
  - 스폰 속도·간격

난이도:
  - 최대 적 수, 적 체력, 점수 기준
  - 게임 속도 배율 (시간에 따라 증가하는 경우)
  - 아이템 등장 확률

비주얼:
  - 색상 팔레트 (COLOR 상수)
  - 배경색, 플레이어색, 적색
  - 파티클 효과 추가/제거

게임플레이:
  - 새 무기/공격 방식 추가
  - 새 적 유형 추가
  - 새 아이템 타입 추가
  - 게임 오버 조건 변경

사운드:
  - 기존 SFX 함수 교체
  - BGM 템포/음계 변경

─────────────────────────────────────────
■ 절대 규칙
─────────────────────────────────────────
RULE-MOD-01: 수정 전 반드시 Read 도구로 기존 game.html 전체를 읽는다.
RULE-MOD-02: 수정 후 Write 도구로 game.html을 저장한다 (덮어쓰기).
RULE-MOD-03: 수정한 내용을 modify_report.md 파일에 기록한다.
             형식:
             # 수정 보고서
             ## 요청
             (수정 요청 내용)
             ## 변경 사항
             - [항목]: 변경 전 → 변경 후
             ## 영향 범위
             (변경으로 인해 같이 조정된 부분)
RULE-MOD-04: TODO, FIXME 같은 미완성 표시를 남기지 않는다.
RULE-MOD-05: 수정 후에도 게임이 완전히 실행 가능한 상태여야 한다.
RULE-MOD-06: 요청한 내용이 기술적으로 불가능하거나 게임을 망가뜨릴 위험이 있으면
             modify_report.md에 이유를 명시하고, 가능한 대안을 제시한다.
"""


async def _run_modifier(game_html: str, changes: str, output_path: str,
                        report_path: str) -> str:
    prompt = f"""아래 게임 코드에 수정 요청을 적용하라.

─────────────────────────────────────────
수정 요청
─────────────────────────────────────────
{changes}

─────────────────────────────────────────
출력 경로
─────────────────────────────────────────
게임 파일: {output_path}
수정 보고서: {report_path}

─────────────────────────────────────────
기존 게임 코드 (game.html)
─────────────────────────────────────────
{game_html}

─────────────────────────────────────────
지시사항
─────────────────────────────────────────
1. 위 수정 요청을 분석한다.
2. 코드에서 수정이 필요한 부분을 정확히 찾는다.
3. 최소 변경 원칙에 따라 수정을 적용한다.
4. Write 도구로 수정된 game.html을 {output_path}에 저장한다.
5. Write 도구로 수정 보고서를 {report_path}에 저장한다.
6. "✅ 수정 완료" 메시지를 출력한다.
"""

    result_text = ""
    async for msg in agent_query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=["Write", "Read"],
            disallowed_tools=["Bash", "computer"],
            system_prompt=SYSTEM,
            cwd=str(Path(output_path).parent),
        ),
    ):
        if isinstance(msg, ResultMessage):
            result_text = (msg.result or "").strip()
    return result_text


def modify(output_dir: str, changes: str) -> bool:
    """
    기존 game.html을 수정하여 덮어쓴다.
    Returns: True(성공) / False(실패)
    """
    out_path   = Path(output_dir)
    game_path  = out_path / "game.html"
    report_path = out_path / "modify_report.md"

    if not game_path.exists():
        print(f"ERROR: {game_path} 없음", flush=True)
        return False

    game_html = game_path.read_text(encoding="utf-8")

    asyncio.run(_run_modifier(
        game_html=game_html,
        changes=changes,
        output_path=str(game_path),
        report_path=str(report_path),
    ))

    return game_path.exists() and game_path.stat().st_size > 500
