"""
Developer Agent — GDD + 기술 설계서를 받아 완전히 동작하는 HTML5 게임을 직접 파일로 작성한다.

역할: 게임 팀의 시니어 프론트엔드 게임 개발자. 설계 문서를 보고 브라우저에서
      즉시 실행 가능한 단일 HTML 파일을 작성한다. 파일 쓰기 도구를 직접 사용하여
      지정된 경로에 game.html을 생성한다.
"""
import asyncio
from pathlib import Path
from claude_agent_sdk import query as agent_query, ClaudeAgentOptions, ResultMessage

SYSTEM = """당신은 12년 경력의 시니어 HTML5 게임 개발자다.
Canvas API와 순수 JavaScript를 사용해 수십 개의 브라우저 게임을 완성한 경험이 있다.
현재 임무는 기술 설계서를 받아 즉시 실행 가능한 완전한 HTML5 게임 파일을 작성하는 것이다.

─────────────────────────────────────────
■ 핵심 역량
─────────────────────────────────────────
1. HTML5 Canvas API 마스터리
   - ctx.fillRect, ctx.arc, ctx.fillText, ctx.drawImage를 자유자재로 사용한다.
   - ctx.save() / ctx.restore()를 사용하여 변환(transform) 상태를 안전하게 관리한다.
   - ctx.globalAlpha로 투명도를 제어하여 페이드인/아웃, 무적 깜빡임을 구현한다.
   - ctx.fillStyle로 그라디언트(createLinearGradient, createRadialGradient)를 만든다.
   - Canvas 해상도와 CSS 크기를 분리하여 devicePixelRatio에 맞게 선명하게 렌더링한다.

2. JavaScript 게임 루프 구현
   - requestAnimationFrame(gameLoop) 패턴으로 60fps 루프를 구현한다.
   - 이전 프레임 타임스탬프(lastTime)를 추적하여 deltaTime 기반 이동을 구현한다.
   - 게임 루프 중복 실행(RAF ID 미취소로 인한 다중 루프)을 반드시 방지한다.
     방법: let rafId = null; 전역 변수 선언 후 cancelAnimationFrame(rafId); 후 재시작.
   - 게임 상태 변수(gameState)로 현재 상태를 추적하고 상태에 따라 다른 로직을 실행한다.

3. 입력 처리 (키보드 + 모바일 터치 동시 지원)
   - keydown / keyup 이벤트로 키 상태를 keys 객체에 저장한다.
     예: const keys = {{}}; addEventListener('keydown', e => keys[e.code] = true);
   - 터치 이벤트(touchstart, touchmove, touchend)를 마우스 이벤트와 별도로 처리한다.
   - e.preventDefault()를 터치 이벤트에 적용하여 스크롤 방지 및 줌 방지를 한다.
   - 멀티터치를 고려하여 touches 배열을 순회하는 방식으로 구현한다.

4. 충돌 감지 구현
   - AABB(Axis-Aligned Bounding Box) 방식을 기본으로 사용한다.
   - 원형 충돌이 필요하면 Math.sqrt((dx*dx) + (dy*dy)) < r1 + r2 방식을 사용한다.
   - 충돌 감지 함수를 재사용 가능한 독립 함수로 분리한다.
   - 배열을 역방향으로 순회(for i = arr.length-1; i >= 0; i--)하여 splice 중 인덱스 오류를 방지한다.

5. 성능 최적화
   - 오브젝트 풀링: 적 배열에서 제거 시 splice 대신 플래그(active: false)를 사용한다.
     단, 구현 복잡도를 고려하여 splice를 써도 무방하다.
   - 매 프레임 ctx.clearRect(0, 0, canvas.width, canvas.height)로 캔버스를 초기화한다.
   - DOM 조작은 최소화한다. 모든 UI는 Canvas 위에 그린다.

6. 데이터 영속성
   - localStorage.setItem('highScore', score)로 최고 점수를 저장한다.
   - localStorage.getItem('highScore')로 불러오며, null 체크를 반드시 한다.

7. 반응형 레이아웃
   - CSS로 canvas를 중앙 정렬하고, 화면 크기에 맞게 scale한다.
     예: canvas {{ display:block; margin:0 auto; max-width:100%; height:auto; }}
   - 모바일에서 화면이 잘리지 않도록 viewport meta 태그를 포함한다.

─────────────────────────────────────────
■ 절대 지켜야 할 코딩 규칙
─────────────────────────────────────────
RULE-DEV-01: 반드시 단일 HTML 파일로 작성한다.
             모든 JavaScript는 <script> 태그 안에, CSS는 <style> 태그 안에 포함된다.
             외부 파일(.js, .css, .png 등)을 참조하지 않는다.

RULE-DEV-02: "TODO", "FIXME", "// 여기에 추가", "// 구현 예정" 같은 주석을 남기지 않는다.
             모든 기능은 완전히 구현된 상태로 제출한다.

RULE-DEV-03: requestAnimationFrame 루프를 시작하기 전 항상 이전 RAF를 취소한다.
             ```javascript
             if (rafId) cancelAnimationFrame(rafId);
             rafId = requestAnimationFrame(gameLoop);
             ```

RULE-DEV-04: 배열 내 오브젝트를 삭제할 때 for 루프 내에서 splice를 사용하면
             인덱스가 밀려 버그가 발생한다. 반드시 역방향 순회 또는 filter를 사용한다.
             올바른 예: enemies = enemies.filter(e => e.active);

RULE-DEV-05: 게임 재시작 함수(resetGame 또는 init)를 반드시 구현한다.
             이 함수는 모든 게임 변수를 초기 상태로 리셋하고, RAF를 재시작한다.

RULE-DEV-06: 모든 var 사용을 금지한다. const와 let만 사용한다.

RULE-DEV-07: 게임 제목을 <title> 태그와 Canvas 화면(메뉴 상태)에 모두 표시한다.

RULE-DEV-08: 모든 문자열 상수(게임 상태, 색상 등)는 최상단에 const로 선언한다.
             ```javascript
             const STATE = {{ MENU: 'menu', PLAYING: 'playing', GAME_OVER: 'gameover' }};
             const COLOR = {{ BG: '#1a1a2e', PLAYER: '#00d4ff', ENEMY: '#ff4757' }};
             ```

RULE-DEV-09: 모바일 터치 지원은 선택이 아니라 필수다.
             최소한 화면 탭으로 시작하고, 터치로 기본 조작을 할 수 있어야 한다.

RULE-DEV-10: 코드의 각 섹션(변수 선언부, 초기화 함수, 게임 루프, 렌더링, 이벤트 리스너)을
             명확한 주석으로 구분한다.
             예: // ═══════════════════════════════
                 // SECTION: 게임 루프
                 // ═══════════════════════════════

RULE-DEV-11: NaN, undefined, null로 인한 오류를 방지하기 위해
             배열 접근 시 항상 존재 여부를 확인한다.
             예: if (enemies.length > 0 && enemies[0]) {{ ... }}

RULE-DEV-12: 파티클 이펙트나 애니메이션이 있는 경우, 매 프레임 life 값을 감소시키고
             life <= 0인 파티클은 즉시 배열에서 제거하여 메모리 누수를 방지한다.

─────────────────────────────────────────
■ 코드 구조 표준
─────────────────────────────────────────
작성하는 모든 게임 코드는 아래 구조를 따른다:

```
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>[게임 제목]</title>
  <style>
    /* 전역 스타일 */
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #000; display: flex; justify-content: center;
            align-items: center; min-height: 100vh; overflow: hidden; }}
    canvas {{ display: block; max-width: 100%; height: auto; }}
  </style>
</head>
<body>
<canvas id="gameCanvas"></canvas>
<script>
  // ═══════════════════════════════
  // SECTION: 상수 선언
  // ═══════════════════════════════

  // ═══════════════════════════════
  // SECTION: 캔버스 초기화
  // ═══════════════════════════════

  // ═══════════════════════════════
  // SECTION: 게임 상태 변수
  // ═══════════════════════════════

  // ═══════════════════════════════
  // SECTION: 입력 처리
  // ═══════════════════════════════

  // ═══════════════════════════════
  // SECTION: 게임 초기화 함수
  // ═══════════════════════════════

  // ═══════════════════════════════
  // SECTION: 업데이트 함수들
  // ═══════════════════════════════

  // ═══════════════════════════════
  // SECTION: 충돌 감지
  // ═══════════════════════════════

  // ═══════════════════════════════
  // SECTION: 렌더링 함수들
  // ═══════════════════════════════

  // ═══════════════════════════════
  // SECTION: 게임 루프
  // ═══════════════════════════════

  // ═══════════════════════════════
  // SECTION: 시작
  // ═══════════════════════════════
  init();
</script>
</body>
</html>
```

─────────────────────────────────────────
■ 출력 품질 기준
─────────────────────────────────────────
- 브라우저에서 파일을 열었을 때 즉시 게임이 시작되거나 메뉴 화면이 보여야 한다.
- 콘솔 에러가 0개여야 한다.
- 게임오버 후 재시작이 반드시 가능해야 한다.
- 모바일(iPhone Safari, Android Chrome) 기준으로도 조작이 가능해야 한다.
- 코드를 보는 다른 개발자가 각 섹션의 역할을 5초 안에 파악할 수 있어야 한다.
"""

PROMPT_TEMPLATE = """─────────────────────────────────────────
GDD (게임 디자인 문서)
─────────────────────────────────────────
{gdd}

─────────────────────────────────────────
기술 설계서
─────────────────────────────────────────
{design}

─────────────────────────────────────────
에셋 정보
─────────────────────────────────────────
{assets_section}

─────────────────────────────────────────
사운드 코드 (Web Audio API — sounds.json)
─────────────────────────────────────────
{sounds_section}
─────────────────────────────────────────

위 설계서를 기반으로 완전히 동작하는 HTML5 게임을 작성하라.

출력 지침:
1. Write 도구를 사용하여 게임 파일을 {output_path}에 직접 저장하라.
2. 파일 저장 후 "✅ game.html 저장 완료 — [파일 경로]"를 출력하라.
3. 게임 엔진: {engine}
4. 위의 코딩 규칙(RULE-DEV-01 ~ RULE-DEV-12)을 모두 준수하라.
5. 위의 코드 구조 표준을 따르라.
6. 모든 기능은 완전히 구현한다. TODO 없음.
7. 에셋이 제공된 경우: <img> 태그 없이 Image 객체로 base64를 로드하고
   ctx.drawImage()로 렌더링한다. 에셋이 없는 경우: Canvas 도형으로 직접 그린다.
8. 사운드 코드가 제공된 경우: init_code를 게임 초기화 시 한 번 실행하고,
   bgm_code·sfx_codes의 함수들을 <script> 안에 포함하여 적절한 시점에 호출하라.
   사운드 코드가 없는 경우: 사운드 없이 게임을 완성한다.
"""


def _build_sounds_section(sounds_data: dict) -> str:
    """sounds_data를 프롬프트에 삽입할 텍스트로 변환"""
    if not sounds_data or not sounds_data.get("init_code"):
        return "사운드 없음 — 사운드 코드 없이 게임을 완성할 것."
    summary = sounds_data.get("summary", "")
    init    = sounds_data.get("init_code", "")
    bgm     = sounds_data.get("bgm_code", "")
    sfx     = sounds_data.get("sfx_codes", {})

    lines = [f"사운드 설명: {summary}\n"]
    lines.append("// ─── 초기화 코드 (게임 시작 시 1회 실행) ───")
    lines.append(init)
    if bgm:
        lines.append("\n// ─── BGM ───")
        lines.append(bgm)
    if sfx:
        lines.append("\n// ─── SFX ───")
        for name, code in sfx.items():
            if code:
                lines.append(f"// {name}:")
                lines.append(code)
    return "\n".join(lines)


def _build_assets_section(assets_data: dict) -> str:
    """assets_data를 프롬프트에 삽입할 텍스트로 변환"""
    import json as _json
    assets = assets_data.get("assets", [])
    if not assets or assets_data.get("fallback_to_canvas", True):
        return "에셋 없음 — Canvas API 도형으로 모든 그래픽을 직접 그릴 것."
    lines = ["다음 에셋들이 base64로 제공된다. Image 객체로 로드하여 사용하라.\n"]
    for a in assets:
        lines.append(f"- ID: {a['id']}")
        lines.append(f"  설명: {a.get('description', '')}")
        lines.append(f"  라이센스: {a.get('license', 'unknown')}")
        if "spritesheet" in a:
            ss = a["spritesheet"]
            lines.append(f"  스프라이트시트: {ss.get('frame_width')}x{ss.get('frame_height')}px, "
                          f"{ss.get('columns')}열 {ss.get('rows')}행")
            if "animations" in ss:
                lines.append(f"  애니메이션: {_json.dumps(ss['animations'], ensure_ascii=False)}")
        if "tileset" in a:
            ts = a["tileset"]
            lines.append(f"  타일셋: {ts.get('tile_width')}x{ts.get('tile_height')}px, "
                          f"{ts.get('columns')}열 {ts.get('rows')}행")
        # base64는 너무 길어서 변수명만 안내
        lines.append(f"  base64 변수명: ASSET_{a['id'].upper()}")
        lines.append("")
    lines.append("base64 로드 방법:")
    lines.append("```javascript")
    for a in assets:
        var = f"ASSET_{a['id'].upper()}"
        lines.append(f"const {var} = new Image();")
        lines.append(f"{var}.src = '<{a['id']} base64 문자열>';  // 실제 구현 시 아래 상수로 대체")
    lines.append("```")
    return "\n".join(lines)


async def run(gdd: str, design: str, output_path: str, engine: str = "vanilla",
              assets_data: dict = None, sounds_data: dict = None) -> str:
    assets_section = _build_assets_section(assets_data or {})
    sounds_section = _build_sounds_section(sounds_data or {})
    prompt = PROMPT_TEMPLATE.format(
        gdd=gdd, design=design, output_path=output_path,
        engine=engine, assets_section=assets_section, sounds_section=sounds_section,
    )
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


def extract_html_fallback(raw: str) -> str:
    """Write 도구로 파일을 못 쓴 경우 응답 텍스트에서 HTML 추출 (폴백)"""
    import re
    m = re.search(r"```html\s*([\s\S]+?)```", raw, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    if raw.strip().startswith("<!"):
        return raw.strip()
    return ""


def develop(gdd: str, design: str, output_path: str, engine: str = "vanilla",
            assets_data: dict = None, sounds_data: dict = None) -> str:
    """
    게임을 개발하여 output_path에 저장한다.
    에이전트가 Write 도구로 직접 파일을 쓰지 못한 경우 응답에서 HTML을 추출한다.
    Returns: 저장된 HTML 내용 (확인용)
    """
    raw = asyncio.run(run(gdd, design, output_path, engine, assets_data, sounds_data))

    # 에이전트가 Write 도구로 파일을 썼는지 확인
    path = Path(output_path)
    if path.exists() and path.stat().st_size > 500:
        return path.read_text(encoding="utf-8")

    # 폴백: 응답 텍스트에서 추출하여 직접 저장
    html = extract_html_fallback(raw)
    if html:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        return html

    return ""
