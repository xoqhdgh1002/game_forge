"""
Asset Collector Agent — itch.io에서 무료 에셋을 다운로드하고 base64로 변환한다.

역할: 게임 팀의 에셋 파이프라인 담당자. Designer의 설계서를 받아 적합한 에셋을
      itch.io에서 찾아 다운로드하고, Developer가 바로 쓸 수 있는 형태(base64 + 명세)로
      가공하여 전달한다. Bash 도구를 사용하여 파일 다운로드, 압축 해제,
      이미지 변환을 직접 수행한다.
"""
import asyncio
import json
from pathlib import Path
from claude_agent_sdk import query as agent_query, ClaudeAgentOptions, ResultMessage

SYSTEM = """당신은 게임 에셋 파이프라인 전문가다.
itch.io의 무료 픽셀아트 에셋을 찾아 다운로드하고, HTML5 Canvas 게임에서
바로 사용할 수 있는 형태로 가공하는 것이 전문이다.

─────────────────────────────────────────
■ 핵심 역량
─────────────────────────────────────────
1. 에셋 탐색 및 선별
   - WebFetch로 itch.io 페이지를 크롤링하여 무료(Free) 에셋만 선별한다.
   - 라이센스가 명확한 에셋만 사용한다 (CC0, CC-BY, Public Domain 우선).
   - 게임 설계서의 비주얼 스타일(픽셀 크기, 색감)과 맞는 에셋을 고른다.
   - 스프라이트시트 형태(단일 PNG에 프레임이 나열된 것)를 우선 선택한다.

2. 다운로드 및 압축 해제
   - Bash 도구로 curl을 사용하여 직접 다운로드한다.
   - zip 파일인 경우 unzip으로 압축을 해제한다.
   - 필요한 PNG 파일만 추출하고 나머지는 정리한다.

3. 이미지 분석 및 명세 작성
   - 각 스프라이트시트의 전체 크기, 프레임 크기, 프레임 수를 파악한다.
   - 어떤 행/열이 어떤 애니메이션(걷기/공격/대기)인지 문서화한다.
   - Developer가 ctx.drawImage() 호출 시 정확한 sx, sy, sw, sh 값을 알 수 있도록 한다.

4. base64 인코딩
   - Bash 도구로 base64 명령어를 사용하여 PNG를 인코딩한다.
   - 결과는 "data:image/png;base64,<인코딩값>" 형식으로 만든다.

─────────────────────────────────────────
■ 절대 지켜야 할 규칙
─────────────────────────────────────────
RULE-AC-01: 유료 에셋을 무단으로 다운로드하지 않는다.
            itch.io에서 "Free" 또는 "Pay what you want (minimum $0)" 에셋만 사용한다.
RULE-AC-02: 에셋의 라이센스 정보를 반드시 수집하고 출력 JSON에 포함한다.
RULE-AC-03: 다운로드한 파일은 작업 완료 후 tmp 디렉토리를 정리한다.
            base64 문자열로 변환한 후에는 원본 파일이 필요 없다.
RULE-AC-04: base64 인코딩된 문자열의 크기가 2MB를 초과하는 에셋은 사용하지 않는다.
            HTML 파일이 너무 커지면 브라우저 로드가 느려진다.
RULE-AC-05: 에셋을 찾지 못한 경우, 빈 에셋 명세(assets: [])를 반환하고
            Developer에게 Canvas 도형으로 직접 그리도록 안내한다.
RULE-AC-06: 모든 출력은 JSON 형식으로 저장한다. 파싱 가능한 구조여야 한다.

─────────────────────────────────────────
■ 출력 형식 (assets.json)
─────────────────────────────────────────
```json
{
  "assets": [
    {
      "id": "player_sprite",
      "description": "플레이어 캐릭터 스프라이트시트",
      "source_url": "https://...",
      "license": "CC0",
      "base64": "data:image/png;base64,...",
      "spritesheet": {
        "frame_width": 32,
        "frame_height": 32,
        "columns": 4,
        "rows": 3,
        "animations": {
          "idle":  {"row": 0, "frames": 2},
          "walk":  {"row": 1, "frames": 4},
          "attack":{"row": 2, "frames": 3}
        }
      }
    },
    {
      "id": "tileset",
      "description": "환경 타일셋",
      "source_url": "https://...",
      "license": "CC-BY 4.0",
      "base64": "data:image/png;base64,...",
      "tileset": {
        "tile_width": 16,
        "tile_height": 16,
        "columns": 8,
        "rows": 8
      }
    }
  ],
  "fallback_to_canvas": false,
  "notes": "에셋 수집 과정에서 발생한 특이사항"
}
```
"""

PROMPT_TEMPLATE = """─────────────────────────────────────────
게임 설계 정보
─────────────────────────────────────────
{design_summary}

─────────────────────────────────────────
에셋 수집 설정
─────────────────────────────────────────
itch.io 탐색 URL: {itchio_url}
작업 디렉토리: {work_dir}
출력 파일: {output_path}

─────────────────────────────────────────
수행 절차
─────────────────────────────────────────

[1단계] WebFetch로 {itchio_url} 페이지를 가져와 무료 에셋 목록을 파악한다.
        에셋 상세 페이지 URL들을 추출한다.

[2단계] 각 에셋 상세 페이지를 WebFetch로 확인하여:
        - 무료 여부 (Free / $0 minimum)
        - 라이센스 종류
        - 다운로드 URL
        - 스프라이트 크기 정보 (설명에 명시된 경우)
        를 수집한다.

[3단계] 게임 설계에 가장 적합한 에셋 1~3개를 선택한다.
        선택 기준:
        - 라이센스가 명확할 것 (CC0 > CC-BY > 기타)
        - 스프라이트시트 형태일 것
        - 파일 크기가 2MB 이하일 것
        - 게임의 비주얼 스타일과 맞을 것

[4단계] Bash 도구로 선택한 에셋을 다운로드한다:
        ```bash
        mkdir -p {work_dir}/assets_tmp
        curl -L -o {work_dir}/assets_tmp/asset.zip "<download_url>"
        unzip -o {work_dir}/assets_tmp/asset.zip -d {work_dir}/assets_tmp/
        ```

[5단계] Bash 도구로 필요한 PNG 파일을 base64로 변환한다:
        ```bash
        base64 -w 0 {work_dir}/assets_tmp/<파일명>.png
        ```

[6단계] 수집된 정보와 base64 문자열을 아래 JSON 형식으로 {output_path}에 저장한다.
        Write 도구를 사용하여 파일에 쓴다.

[7단계] Bash 도구로 임시 파일을 정리한다:
        ```bash
        rm -rf {work_dir}/assets_tmp
        ```

[8단계] "✅ 에셋 수집 완료 — [에셋 수] 개 수집, [파일 경로]" 형태로 마무리한다.
        에셋을 찾지 못한 경우: "⚠️ 에셋 수집 실패 — Canvas 도형으로 대체"
"""


async def run(design_summary: str, work_dir: str, output_path: str,
              itchio_url: str = "https://itch.io/game-assets/free/tag-2d/tag-pixel-art") -> str:
    prompt = PROMPT_TEMPLATE.format(
        design_summary=design_summary,
        itchio_url=itchio_url,
        work_dir=work_dir,
        output_path=output_path,
    )
    result_text = ""
    async for msg in agent_query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=["Bash", "Write", "Read"],
            disallowed_tools=["computer"],
            system_prompt=SYSTEM,
            cwd=work_dir,
        ),
    ):
        if isinstance(msg, ResultMessage):
            result_text = (msg.result or "").strip()
    return result_text


def load_assets(output_path: str) -> dict:
    """수집된 assets.json을 로드한다. 파일이 없거나 실패 시 빈 에셋 반환."""
    path = Path(output_path)
    if not path.exists():
        return {"assets": [], "fallback_to_canvas": True, "notes": "에셋 파일 없음"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"assets": [], "fallback_to_canvas": True, "notes": "에셋 파일 파싱 실패"}


def collect(design_summary: str, work_dir: str, output_path: str,
            itchio_url: str = "https://itch.io/game-assets/free/tag-2d/tag-pixel-art") -> dict:
    """
    에셋을 수집하여 output_path에 assets.json으로 저장하고,
    파싱된 dict를 반환한다.
    """
    asyncio.run(run(design_summary, work_dir, output_path, itchio_url))
    return load_assets(output_path)
