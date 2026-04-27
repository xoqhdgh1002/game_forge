"""
Sound Agent — GDD를 읽고 게임에 맞는 Web Audio API 사운드 코드를 생성한다.

역할: 게임 사운드 디자이너. GDD와 design.md를 분석하여
      게임의 분위기와 메카닉에 맞는 BGM·효과음을 Web Audio API JavaScript 코드로 작성한다.
      외부 오디오 파일 없이 브라우저에서 직접 합성하는 코드를 생성한다.

출력: sounds.json
  {
    "bgm_code":    "<JS 함수 — 배경음악 생성>",
    "sfx_codes":   {"jump": "<JS>", "shoot": "<JS>", ...},
    "init_code":   "<AudioContext 초기화 JS>",
    "summary":     "어떤 사운드를 만들었는지 한 줄 설명"
  }
"""
import asyncio
import json
from pathlib import Path

from claude_agent_sdk import query as agent_query, ClaudeAgentOptions, ResultMessage

SYSTEM = """당신은 Web Audio API 전문 사운드 디자이너이자 JavaScript 개발자다.
브라우저에서 외부 오디오 파일 없이 순수 코드로 게임 사운드를 생성하는 전문가다.

─────────────────────────────────────────
■ 핵심 역량
─────────────────────────────────────────
1. Web Audio API 완전 이해
   - AudioContext, OscillatorNode, GainNode, BiquadFilterNode를 능숙하게 조합한다.
   - 복잡한 음색을 만들기 위해 여러 오실레이터를 겹쳐 사용한다.
   - ADSR(Attack-Decay-Sustain-Release) 엔벨로프로 자연스러운 소리를 만든다.
   - Chiptune, Retro 8bit 스타일 사운드를 코드만으로 구현한다.

2. 게임 장르별 사운드 설계
   - 플랫포머: 통통 튀는 점프음, 코인 수집음, 레트로 BGM
   - 슈팅게임: 레이저/총격음, 폭발음, 빠른 긴박감의 BGM
   - 퍼즐: 부드러운 클릭음, 성공 팡파레, 잔잔한 앰비언트 BGM
   - RPG: 스텝 사운드, 전투 효과음, 웅장한 메인 테마

3. 성능 최적화
   - AudioContext는 싱글턴으로 관리한다.
   - 사용 후 노드는 disconnect()로 정리하여 메모리 누수를 방지한다.
   - 모바일 정책상 첫 사용자 인터랙션 이후에만 AudioContext를 시작한다.

─────────────────────────────────────────
■ 출력 형식 (JSON)
─────────────────────────────────────────
반드시 아래 JSON 구조를 ```json ... ``` 블록으로 출력한다:

{
  "summary": "어떤 사운드를 생성했는지 한 줄 설명",
  "init_code": "// AudioContext 초기화 및 공통 유틸 함수 (전역 실행)",
  "bgm_code": "// BGM 재생 함수: function playBGM() { ... }",
  "sfx_codes": {
    "jump":      "// function sfxJump() { ... }",
    "shoot":     "// function sfxShoot() { ... }",
    "hit":       "// function sfxHit() { ... }",
    "game_over": "// function sfxGameOver() { ... }",
    "collect":   "// function sfxCollect() { ... }",
    "level_up":  "// function sfxLevelUp() { ... }"
  }
}

─────────────────────────────────────────
■ 코드 품질 규칙
─────────────────────────────────────────
RULE-SND-01: 모든 함수는 독립적으로 호출 가능해야 한다.
             의존성은 오직 AudioContext 싱글턴(전역 변수 audioCtx)뿐이다.
RULE-SND-02: 각 sfx 함수는 50ms~500ms 이내의 짧은 사운드를 생성한다.
             BGM은 루프 가능한 2~4마디 길이로 작성한다.
RULE-SND-03: try-catch로 감싸서 사운드 오류가 게임을 멈추지 않게 한다.
RULE-SND-04: 모바일 AutoPlay 정책을 반드시 고려한다.
             AudioContext.state === 'suspended' 체크 후 resume()을 호출한다.
RULE-SND-05: BGM에는 반드시 stopBGM() 함수도 함께 작성한다.
RULE-SND-06: 장르에 맞는 음계와 리듬을 사용한다.
             RPG는 장조, 호러는 단조, 퍼즐은 밝고 경쾌하게.
RULE-SND-07: 게임에 등장하지 않는 사운드(shoot이 없는 퍼즐 등)는 해당 key를 null로 둔다.
RULE-SND-08: 실제 동작하는 완전한 코드를 작성한다. "// 여기에 구현" 주석은 절대 금지.
"""


async def _run_sound(gdd: str, design_doc: str) -> dict:
    prompt = f"""아래 GDD와 설계 문서를 분석하고,
이 게임에 어울리는 Web Audio API 사운드를 설계하라.

─────────────────────────────────────────
GDD (게임 디자인 문서):
─────────────────────────────────────────
{gdd}

─────────────────────────────────────────
설계 문서 (design.md):
─────────────────────────────────────────
{design_doc}

─────────────────────────────────────────
요구사항:
─────────────────────────────────────────
1. 게임의 장르, 분위기, 메카닉을 파악한다.
2. 적합한 BGM과 SFX를 Web Audio API 코드로 작성한다.
3. 반드시 ```json ... ``` 블록으로 출력한다.
4. 게임에 존재하지 않는 사운드(예: 퍼즐에 shoot)는 null로 남긴다.
"""

    result_text = ""
    async for msg in agent_query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=[],
            disallowed_tools=["Bash", "computer"],
            system_prompt=SYSTEM,
        ),
    ):
        if isinstance(msg, ResultMessage):
            result_text = (msg.result or "").strip()

    # JSON 블록 파싱
    import re
    m = re.search(r"```json\s*(\{[\s\S]+?\})\s*```", result_text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # fallback: 응답 전체에서 JSON 추출 시도
    try:
        start = result_text.index("{")
        end   = result_text.rindex("}") + 1
        return json.loads(result_text[start:end])
    except Exception:
        return {}


def create_sounds(gdd: str, design_doc: str) -> dict:
    """사운드 코드를 생성하여 dict를 반환한다. 실패 시 빈 dict."""
    return asyncio.run(_run_sound(gdd, design_doc))
