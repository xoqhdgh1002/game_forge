"""
Orchestrator Agent — 게임 개발 팀 총지휘관 v3

역할: forge.py / bot.py로부터 작업 지시를 받아
      Producer → Designer → [Sound + Asset(병렬)] → Developer → QA 루프를
      Claude 에이전트가 상황에 따라 판단하며 지휘한다.

v3 개선사항:
  - Phase 2 구조 수정: Designer 완료 후 Sound + Asset 병렬 실행
    (Sound Agent가 design.md를 필요로 하므로 Designer보다 먼저 실행 불가)
  - 파이프라인 상태 저장 (pipeline_state.json) — 강제 종료 후 복구 가능
  - 텔레그램 실시간 진행 알림 (notify.py)
  - Developer가 sounds.json을 읽어 사운드 통합
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from claude_agent_sdk import query as agent_query, ClaudeAgentOptions, ResultMessage

PYTHON     = str(Path(sys.executable))
AGENTS_DIR = str(Path(__file__).parent / "agents")


# ── 파이프라인 상태 관리 ─────────────────────────────────────────────────────
def _save_state(output_dir: str, state: dict):
    """파이프라인 현재 상태를 pipeline_state.json에 저장한다."""
    try:
        p = Path(output_dir) / "pipeline_state.json"
        state["updated_at"] = datetime.now().isoformat()
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_state(output_dir: str) -> dict | None:
    """저장된 파이프라인 상태를 읽는다. 없으면 None."""
    try:
        p = Path(output_dir) / "pipeline_state.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None

SYSTEM = f"""당신은 HTML5 게임 개발 팀의 수석 오케스트레이터다.
주어진 작업 디렉토리 안에서 각 에이전트 CLI를 Bash로 호출하여 게임을 완성하는 것이
당신의 유일한 임무다.

─────────────────────────────────────────
■ 사용 가능한 에이전트 CLI 명령어
─────────────────────────────────────────
Python 인터프리터: {PYTHON}
에이전트 디렉토리: {AGENTS_DIR}

1. Producer — GDD 초안 생성
   명령어: {PYTHON} {AGENTS_DIR}/run_producer.py "<idea>" "<style>" "<engine>" "<output_dir>"
   출력: <output_dir>/gdd.md
   성공: "OK:" 로 시작하는 stdout, exit 0

2. Designer — 세부 기술 설계
   명령어: {PYTHON} {AGENTS_DIR}/run_designer.py "<output_dir>"
   입력: <output_dir>/gdd.md
   출력: <output_dir>/design.md
   성공: "OK:" 로 시작하는 stdout, exit 0

3. Sound Agent — Web Audio API 사운드 코드 생성 (항상 실행)
   명령어: {PYTHON} {AGENTS_DIR}/run_sound_agent.py "<output_dir>"
   입력: <output_dir>/gdd.md + design.md
   출력: <output_dir>/sounds.json
   성공: "OK:" 또는 "FALLBACK:" (실패 시 기본 비프음 사용), 항상 exit 0

4. Asset Collector — itch.io 에셋 수집 (use_assets=Yes 인 경우만)
   명령어: {PYTHON} {AGENTS_DIR}/run_asset_collector.py "<output_dir>" "<itchio_url>"
   입력: <output_dir>/design.md
   출력: <output_dir>/assets.json
   성공: "OK:" 또는 "FALLBACK:", 항상 exit 0

5. Developer — 게임 코드 작성
   명령어: {PYTHON} {AGENTS_DIR}/run_developer.py "<output_dir>" "<engine>"
   입력: <output_dir>/gdd.md + design.md + sounds.json (+ assets.json)
   출력: <output_dir>/game.html
   성공: "OK:" 로 시작하는 stdout, exit 0

6. QA — 코드 검토 및 수정
   명령어: {PYTHON} {AGENTS_DIR}/run_qa.py "<output_dir>"
   입력: <output_dir>/game.html
   출력: <output_dir>/game.html (수정됨) + qa_report.md
   exit 0: QA 통과 (크리티컬 버그 없음)
   exit 2: 크리티컬 버그 발견 → Developer 재실행 필요

7. 진행 알림 — 텔레그램으로 상태 메시지 전송 (선택)
   명령어: {PYTHON} {AGENTS_DIR}/notify.py "<output_dir>" "<message>"
   실패해도 파이프라인을 멈추지 않는다. 항상 exit 0.

─────────────────────────────────────────
■ 실행 순서 (3단계 파이프라인)
─────────────────────────────────────────

【Phase 1 — 기획】 (순차)
  Producer → gdd.md 생성

  알림: notify.py "✅ 기획 완료! 설계·사운드·에셋 준비 중..."

【Phase 2a — 설계】 (순차)
  Designer → design.md 생성
  ⚠️ Sound Agent는 design.md가 반드시 필요하므로 Designer 완료 전 실행 불가.

  알림: notify.py "🎨 기술 설계 완료! 사운드·에셋 준비 중..."

【Phase 2b — 병렬 준비】 (Sound + Asset 동시 실행, Designer 완료 후)
  Designer가 완료되어 design.md가 생성된 뒤 Sound와 Asset을 병렬 실행한다.

  bash 예시:
  ```
  PYTHON="{PYTHON}"
  AGENTS="{AGENTS_DIR}"
  OUT="<output_dir>"

  # Sound Agent — design.md 완료 후 실행
  "$PYTHON" "$AGENTS/run_sound_agent.py" "$OUT" > "$OUT/sound.log" 2>&1 &
  SOUND_PID=$!

  # Asset Collector (use_assets=Yes일 때만)
  if [ use_assets = Yes ]; then
    "$PYTHON" "$AGENTS/run_asset_collector.py" "$OUT" "<itchio_url>" > "$OUT/asset.log" 2>&1 &
    ASSET_PID=$!
    wait $SOUND_PID $ASSET_PID
  else
    wait $SOUND_PID
  fi
  ```

  각 결과 확인:
  - cat sound.log    → "OK:" 또는 "FALLBACK:"
  - cat asset.log    → "OK:" 또는 "FALLBACK:" (use_assets일 때)

  알림: notify.py "🔊 사운드·에셋 준비 완료! 코드 작성 시작..."

【Phase 3 — 개발 + QA 루프】 (순차, 최대 max_retries 회)
  Developer → QA
    QA exit 0 → 완료
    QA exit 2 → Developer 재실행 (qa_report.md 참고) → QA 재실행
  max_retries 초과 시 현재 game.html 그대로 사용

  알림(각 반복 시작): notify.py "⚙️ 코드 작성 중... (시도 N/max_retries)"
  알림(QA 통과):     notify.py "🔍 QA 통과! 마무리 중..."
  알림(QA 실패 재시도): notify.py "🔧 버그 수정 중... (N회 남음)"

─────────────────────────────────────────
■ 실패 처리
─────────────────────────────────────────
- Producer 실패 (exit 1): 1회 재시도 후 중단
- Designer 실패 (exit 1): 1회 재시도 후 Sound/Asset만으로 진행
- Sound Agent 실패: FALLBACK 확인 후 계속 진행 (사운드 없어도 게임은 완성)
- Asset Collector 실패: FALLBACK 확인 후 계속 진행 (Canvas 도형 사용)
- Developer 실패 (exit 1): 1회 재시도 후 QA 건너뛰고 완료
- QA 실패 (exit 1, not exit 2): QA 건너뛰고 game.html 그대로 완료

─────────────────────────────────────────
■ Developer에게 sounds.json 전달 방법
─────────────────────────────────────────
Developer(run_developer.py)는 자동으로 sounds.json을 읽는다.
오케스트레이터가 직접 sounds.json 내용을 Developer에게 전달할 필요 없다.
단, Developer 실행 전 sounds.json이 <output_dir>에 존재해야 한다.

─────────────────────────────────────────
■ 절대 지켜야 할 규칙
─────────────────────────────────────────
RULE-ORC-01: 각 에이전트 CLI 실행 전 "▶ [에이전트명] 시작..." 을 출력한다.
RULE-ORC-02: 각 에이전트 CLI 실행 후 exit code와 stdout/stderr를 확인한다.
RULE-ORC-03: Phase 2는 반드시 병렬(&)로 실행하여 전체 시간을 단축한다.
RULE-ORC-04: 각 Phase 시작/완료 시 notify.py로 텔레그램 알림을 보낸다.
RULE-ORC-05: 최종적으로 game.html이 존재하면 "✅ 오케스트레이션 완료: <경로>" 를 출력한다.
RULE-ORC-06: game.html이 끝내 생성되지 않으면 "❌ 오케스트레이션 실패" 를 출력하고 exit 1한다.
RULE-ORC-07: 모든 로그는 타임스탬프 [HH:MM:SS] 형식을 앞에 붙인다.
RULE-ORC-08: Sound Agent는 use_assets 여부와 무관하게 항상 실행한다.
"""

PROMPT_TEMPLATE = """─────────────────────────────────────────
오케스트레이션 작업 명세
─────────────────────────────────────────
아이디어: {idea}
스타일:   {style}
엔진:     {engine}
출력 디렉토리: {output_dir}
에셋 수집 여부: {use_assets}
itch.io URL: {itchio_url}
QA 건너뜀: {skip_qa}
최대 재시도 횟수: {max_retries}
─────────────────────────────────────────

위 명세대로 파이프라인을 실행하라.
⚠️ 중요: Phase 2b(Sound + Asset)는 Phase 2a(Designer) 완료 후에만 실행한다.
         Sound Agent가 design.md를 필요로 하기 때문이다.
각 Phase 전후로 notify.py를 호출해 텔레그램에 진행 상황을 알린다.
모든 에이전트 CLI는 Bash 도구로 실행한다.

각 Phase 완료 시 아래 형식으로 pipeline_state.json을 Write 도구로 저장하라:
Phase 1 완료: {{"stage":"designer","idea":"{idea}","style":"{style}","engine":"{engine}"}}
Phase 2a 완료: {{"stage":"sound_asset","idea":"{idea}","style":"{style}","engine":"{engine}"}}
Phase 2b 완료: {{"stage":"developer","idea":"{idea}","style":"{style}","engine":"{engine}"}}
Phase 3 완료: {{"stage":"done","idea":"{idea}","style":"{style}","engine":"{engine}"}}
"""


async def run(
    idea: str,
    style: str,
    engine: str,
    output_dir: str,
    use_assets: bool,
    itchio_url: str,
    skip_qa: bool,
    max_retries: int,
) -> str:
    prompt = PROMPT_TEMPLATE.format(
        idea=idea,
        style=style,
        engine=engine,
        output_dir=output_dir,
        use_assets="Yes" if use_assets else "No",
        itchio_url=itchio_url,
        skip_qa="Yes" if skip_qa else "No",
        max_retries=max_retries,
    )
    result_text = ""
    async for msg in agent_query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=["Bash", "Write", "Read"],
            disallowed_tools=["computer"],
            system_prompt=SYSTEM,
            cwd=output_dir,
        ),
    ):
        if isinstance(msg, ResultMessage):
            result_text = (msg.result or "").strip()
    return result_text


def orchestrate(
    idea: str,
    style: str = "pixel",
    engine: str = "vanilla",
    output_dir: str = ".",
    use_assets: bool = False,
    itchio_url: str = "https://itch.io/game-assets/free/tag-2d/tag-pixel-art",
    skip_qa: bool = False,
    max_retries: int = 2,
) -> bool:
    """
    오케스트레이션을 실행한다.
    Returns: True(성공) / False(실패)
    """
    # 파이프라인 시작 상태 저장
    _save_state(output_dir, {
        "stage": "started",
        "idea": idea,
        "style": style,
        "engine": engine,
        "use_assets": use_assets,
        "skip_qa": skip_qa,
        "max_retries": max_retries,
        "itchio_url": itchio_url,
    })

    result = asyncio.run(run(
        idea=idea,
        style=style,
        engine=engine,
        output_dir=output_dir,
        use_assets=use_assets,
        itchio_url=itchio_url,
        skip_qa=skip_qa,
        max_retries=max_retries,
    ))
    game_html = Path(output_dir) / "game.html"
    success = game_html.exists() and game_html.stat().st_size > 500

    # 최종 상태 저장
    _save_state(output_dir, {
        "stage": "done" if success else "failed",
        "idea": idea,
        "style": style,
        "engine": engine,
    })
    return success
