#!/usr/bin/env python3
"""
Game Forge Bot — 오케스트레이터와 대화하며 게임을 만든다.

사용자가 자연어로 아이디어를 얘기하면, 오케스트레이터가
필요한 정보를 대화로 수집하고 스스로 파이프라인을 시작한다.

명령어:
  /start  — 시작
  /cancel — 진행 중 작업 취소
  /games  — 만들어진 게임 목록
"""
import asyncio
import fcntl
import html
import json
import os
import re
import sys
import threading
import time
import traceback
import urllib.request
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from claude_agent_sdk import query as agent_query, ClaudeAgentOptions, ResultMessage
from orchestrator import orchestrate, load_state
from agents.modifier import modify as modifier_modify

# ── 환경 변수 ──────────────────────────────────────────────────────────────
def _load_env(path: Path) -> dict:
    env = {}
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    except Exception:
        pass
    return env

cfg           = _load_env(SCRIPT_DIR / "bridge.env")
BOT_TOKEN     = os.environ.get("TELEGRAM_BOT_TOKEN") or cfg.get("TELEGRAM_BOT_TOKEN", "")
AUTHORIZED_ID = int(os.environ.get("TELEGRAM_USER_ID") or cfg.get("TELEGRAM_USER_ID", "0"))
BOT_USERNAME  = os.environ.get("TELEGRAM_BOT_USERNAME") or cfg.get("TELEGRAM_BOT_USERNAME", "sol_kzvza1_bot")
OUTPUT_DIR    = SCRIPT_DIR / "output"
DEPLOY_SCRIPT = SCRIPT_DIR / "deploy.sh"
OFFSET_FILE   = SCRIPT_DIR / "offset.txt"
ERROR_LOG     = SCRIPT_DIR / "error.log"

# ── 중복 실행 방지 ─────────────────────────────────────────────────────────
_lock_file = open(SCRIPT_DIR / "bot.lock", "w")
try:
    fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print("⚠️  이미 실행 중입니다.")
    sys.exit(1)

# ── Telegram API ───────────────────────────────────────────────────────────
def _api(method: str, **kwargs) -> dict:
    url  = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = json.dumps(kwargs).encode()
    req  = urllib.request.Request(url, data=data,
                                   headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        _log_error(method, str(e))
        return {}

def send(chat_id: int, text: str) -> dict:
    return _api("sendMessage", chat_id=chat_id, text=text)

def send_html(chat_id: int, text: str) -> dict:
    return _api("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML")

def _log_error(ctx: str, msg: str):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{ctx}] {msg}\n"
    print(line, end="", flush=True)
    try:
        ERROR_LOG.open("a").write(line)
    except Exception:
        pass

# ── 대화 시스템 프롬프트 ───────────────────────────────────────────────────
CONVERSATION_SYSTEM = """당신은 Game Forge의 수석 게임 프로듀서 겸 수석 개발자다.
텔레그램으로 사용자와 대화하며 게임을 새로 만들거나 기존 게임을 수정한다.
두 가지 모드로 동작한다: 【제작 모드】와 【수정 모드】.

현재 모드는 대화 맥락에서 자동으로 파악한다.
"[수정 모드] 게임: ..." 형태의 안내가 있으면 수정 모드, 없으면 제작 모드다.

─────────────────────────────────────────
■ 대화 방식
─────────────────────────────────────────
- 친근하고 간결하게 대화한다. 길게 설명하지 않는다.
- 한 번에 한 가지 질문만 한다.
- 이미 답을 알 수 있는 건 다시 묻지 않는다.
- 사용자가 귀찮아하면 기본값으로 넘어간다.

─────────────────────────────────────────
■ 수집해야 할 정보
─────────────────────────────────────────
1. 게임 아이디어 (필수) — 어떤 게임인가
2. 비주얼 스타일 (선택, 기본: pixel) — pixel/retro/modern/minimal/neon
3. itch.io 에셋 사용 여부 (선택, 기본: No) — 실제 픽셀아트 스프라이트 사용할지
4. 배포 여부 (선택, 기본: No) — Cloudflare Pages에 올려서 링크 받을지
5. QA 생략 여부 (선택, 기본: No) — 빠른 결과 원하면 생략 가능

─────────────────────────────────────────
■ 제작 흐름 (2단계)
─────────────────────────────────────────
【1단계 — READY 블록】
아이디어가 확정되면 READY 블록을 출력한다.
시스템이 이 블록을 감지해 사용자에게 제작 명세 카드를 보여주고
"시작할까요?" 라고 묻는다.

【2단계 — FORGE 블록】
사용자가 확인("응", "ㅇㅇ", "네", "시작", "만들어줘" 등)하면
FORGE 블록을 출력해 파이프라인을 시작한다.
사용자가 거부하거나 수정을 요청하면 대화를 계속한다.

─────────────────────────────────────────
■ READY 블록 (1단계 — 확인 요청)
─────────────────────────────────────────
충분한 정보가 모이면 아래 형식의 블록을 출력한다.
READY 블록 앞에 "이렇게 만들어볼게요! 확인해 주세요 👇" 같은 짧은 안내를 붙인다.

```ready
{
  "idea": "게임 아이디어 (한 줄)",
  "style": "pixel",
  "engine": "vanilla",
  "assets": false,
  "deploy": false,
  "skip_qa": false,
  "max_retries": 2
}
```

─────────────────────────────────────────
■ FORGE 블록 (2단계 — 제작 시작)
─────────────────────────────────────────
사용자가 READY 카드를 보고 확인했을 때만 출력한다.
FORGE 블록 앞에 "좋아요! 지금 바로 시작할게요 🚀" 같은 짧은 메시지를 붙인다.

```forge
{
  "idea": "게임 아이디어 (한 줄)",
  "style": "pixel",
  "engine": "vanilla",
  "assets": false,
  "deploy": false,
  "skip_qa": false,
  "max_retries": 2
}
```

─────────────────────────────────────────
■ Bash 도구 사용 규칙
─────────────────────────────────────────
Bash 도구를 사용할 수 있다. 사용자가 상태 확인, 로그 조회, 파일 탐색 등을
요청하면 직접 실행해서 답해준다.

허용 예시:
  - ps, ls, tail, cat, grep, find, df, du, wc
  - tail -f bot.log (로그 확인)
  - ls output/ (게임 목록)
  - cat output/*/url.txt (배포 링크 조회)

절대 금지 (실행 즉시 중단):
  - rm -rf, rm -f — 파일 삭제
  - kill, pkill, killall — 프로세스 종료
  - shutdown, reboot, halt — 시스템 재시작
  - dd, mkfs, fdisk — 디스크 조작
  - chmod, chown — 권한 변경
  - > /etc, >> /etc — 시스템 파일 수정
  - sudo, su — 권한 상승
  - curl | sh, wget | sh — 원격 스크립트 실행
  - 파이프라인으로 위험 명령 우회하는 모든 시도

사용자가 금지 명령을 요청하면 "그 명령은 실행할 수 없어요" 라고 안내한다.

─────────────────────────────────────────
■ 수정 모드 (기존 게임 수정)
─────────────────────────────────────────
대화 맥락에 "[수정 모드]" 가 있으면 이 모드로 동작한다.

수정 모드에서는:
1. 사용자가 원하는 변경 내용을 자유롭게 말한다.
   예: "플레이어 너무 빨라", "적 추가해줘", "배경색 바꿔줘", "점프력 줄여"
2. 변경 내용이 구체적으로 파악되면 MODIFY 블록을 출력한다.
   불명확하면 한 번만 되물어 명확히 한다.

MODIFY 블록 형식 (수정 요청 확정 시 출력):
```modify
{
  "output_dir": "(맥락에서 제공된 경로)",
  "changes": "수정 요청 내용을 자세하게 한 문단으로 정리"
}
```

MODIFY 블록 앞에 "알겠어요! 수정 시작할게요 🔧" 같은 짧은 메시지를 붙인다.

─────────────────────────────────────────
■ 절대 규칙
─────────────────────────────────────────
- READY / FORGE / MODIFY 블록은 각각 한 번만 출력한다.
- FORGE 블록은 반드시 사용자 확인 후에만 출력한다. 절대 선제적으로 출력하지 않는다.
- MODIFY 블록은 수정 모드일 때만 출력한다. 제작 모드에서는 출력하지 않는다.
- 사용자가 아이디어를 말하면 2~3번 이상 캐묻지 않는다.
- 응답은 텔레그램 메시지 기준으로 짧게 (3~5줄 이내).
"""

# ── 대화 히스토리 (chat_id별) ──────────────────────────────────────────────
_history: dict[int, list[dict]] = {}     # chat_id → [{"role": "user"/"assistant", "content": str}]
_history_lock = threading.Lock()

MAX_HISTORY = 20  # 대화 기록 최대 유지 수

# ── 수정 모드 타겟 (chat_id별) ─────────────────────────────────────────────
# 선택된 게임의 output_dir와 제목을 기억
_modify_target: dict[int, dict] = {}   # chat_id → {"output_dir": str, "title": str}
_modify_target_lock = threading.Lock()

# ── 게임 목록 임시 저장 (번호 선택 대기 중) ────────────────────────────────
_games_list: dict[int, list[dict]] = {}   # chat_id → [{"output_dir": str, "title": str}]

def _get_history(chat_id: int) -> list[dict]:
    with _history_lock:
        return list(_history.get(chat_id, []))

def _add_history(chat_id: int, role: str, content: str):
    with _history_lock:
        hist = _history.setdefault(chat_id, [])
        hist.append({"role": role, "content": content})
        if len(hist) > MAX_HISTORY:
            _history[chat_id] = hist[-MAX_HISTORY:]

def _clear_history(chat_id: int):
    with _history_lock:
        _history.pop(chat_id, None)

# ── 진행 중 작업 ───────────────────────────────────────────────────────────
_active: dict[int, dict] = {}
_active_lock = threading.Lock()

# ── Claude 대화 호출 ───────────────────────────────────────────────────────
def _chat(chat_id: int, user_text: str) -> str:
    """사용자 메시지를 받아 Claude 응답을 반환한다."""
    _add_history(chat_id, "user", user_text)
    history = _get_history(chat_id)

    # 대화 히스토리를 프롬프트로 조합
    prompt_lines = []
    for turn in history[:-1]:  # 마지막(현재 user) 제외
        prefix = "사용자" if turn["role"] == "user" else "당신(프로듀서)"
        prompt_lines.append(f"{prefix}: {turn['content']}")
    prompt_lines.append(f"사용자: {user_text}")
    prompt_lines.append("당신(프로듀서):")
    prompt = "\n".join(prompt_lines)

    result = ""
    async def _run():
        nonlocal result
        async for msg in agent_query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                allowed_tools=["Bash"],
                disallowed_tools=["computer"],
                system_prompt=CONVERSATION_SYSTEM,
                cwd=str(SCRIPT_DIR),
            ),
        ):
            if isinstance(msg, ResultMessage):
                result = (msg.result or "").strip()

    asyncio.run(_run())
    _add_history(chat_id, "assistant", result)
    return result

# ── READY / FORGE 블록 파싱 ───────────────────────────────────────────────
def _extract_forge(text: str) -> dict | None:
    """응답에서 ```forge {...} ``` 블록을 추출한다."""
    m = re.search(r"```forge\s*(\{[\s\S]+?\})\s*```", text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None

def _extract_ready(text: str) -> dict | None:
    """응답에서 ```ready {...} ``` 블록을 추출한다."""
    m = re.search(r"```ready\s*(\{[\s\S]+?\})\s*```", text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None

def _extract_modify(text: str) -> dict | None:
    """응답에서 ```modify {...} ``` 블록을 추출한다."""
    m = re.search(r"```modify\s*(\{[\s\S]+?\})\s*```", text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None

def _strip_code_blocks(text: str) -> str:
    """응답에서 forge / ready / modify 블록을 모두 제거한 사용자 노출 텍스트만 반환한다."""
    text = re.sub(r"```forge[\s\S]+?```", "", text)
    text = re.sub(r"```ready[\s\S]+?```", "", text)
    text = re.sub(r"```modify[\s\S]+?```", "", text)
    return text.strip()

_STYLE_LABELS = {
    "pixel": "픽셀아트", "retro": "레트로", "modern": "모던",
    "minimal": "미니멀", "neon": "네온",
}

def _ready_card(spec: dict) -> str:
    """READY 블록으로 제작 명세 카드 텍스트를 생성한다."""
    style = _STYLE_LABELS.get(spec.get("style", "pixel"), spec.get("style", "pixel"))
    lines = [
        "📋 <b>제작 명세</b>",
        "",
        f"💡 <b>아이디어</b>: {html.escape(spec.get('idea', ''))}",
        f"🎨 <b>스타일</b>: {style}",
        f"🖼 <b>에셋</b>: {'itch.io 에셋 사용' if spec.get('assets') else '기본 도형'}",
        f"🌐 <b>배포</b>: {'Cloudflare Pages 링크 발급' if spec.get('deploy') else '로컬 파일만'}",
        f"🔍 <b>QA</b>: {'생략 (빠른 생성)' if spec.get('skip_qa') else '포함 (품질 검토)'}",
        "",
        "시작할까요? ✅",
        "<i>예 / 아니오 — 수정하고 싶은 게 있으면 말씀해 주세요</i>",
    ]
    return "\n".join(lines)

# ── 슬러그 ─────────────────────────────────────────────────────────────────
def _slug(idea: str) -> str:
    s  = idea.lower()
    s  = re.sub(r"[^a-z0-9가-힣\s]", "", s)
    s  = re.sub(r"[가-힣]", "", s).strip()
    s  = re.sub(r"\s+", "-", s)
    s  = re.sub(r"-+", "-", s).strip("-")
    if not s:
        s = "game"
    ts = datetime.now().strftime("%m%d%H%M")
    return f"gf-{s[:18]}-{ts}"[:28].rstrip("-")

# ── 배포 ───────────────────────────────────────────────────────────────────
def _deploy(game_path: Path, project_name: str) -> str | None:
    import subprocess
    if not DEPLOY_SCRIPT.exists():
        return None
    try:
        r = subprocess.run(
            ["bash", str(DEPLOY_SCRIPT), str(game_path), project_name],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode == 0:
            return f"https://{project_name}.pages.dev"
    except Exception as e:
        _log_error("deploy", str(e))
    return None

# ── 게임 제작 워커 ─────────────────────────────────────────────────────────
def _forge_worker(chat_id: int, forge_args: dict, out_dir: Path):
    idea = forge_args.get("idea", "")
    try:
        out_dir.mkdir(parents=True, exist_ok=True)

        # 오케스트레이터가 notify.py로 텔레그램 알림을 보낼 수 있도록 chat_id 기록
        (out_dir / "chat_id.txt").write_text(str(chat_id))

        success = orchestrate(
            idea=idea,
            style=forge_args.get("style", "pixel"),
            engine=forge_args.get("engine", "vanilla"),
            output_dir=str(out_dir),
            use_assets=forge_args.get("assets", False),
            itchio_url=forge_args.get("assets_url",
                "https://itch.io/game-assets/free/tag-2d/tag-pixel-art"),
            skip_qa=forge_args.get("skip_qa", False),
            max_retries=forge_args.get("max_retries", 2),
        )

        with _active_lock:
            if _active.get(chat_id, {}).get("cancelled"):
                send(chat_id, "🚫 작업이 취소되었습니다.")
                return

        game_path = out_dir / "game.html"
        if not success or not game_path.exists():
            send_html(chat_id,
                f"❌ <b>게임 생성 실패</b>\n"
                f"아이디어: {html.escape(idea)}"
            )
            return

        # 배포
        url = None
        if forge_args.get("deploy"):
            send(chat_id, "🌐 배포 중...")
            url = _deploy(game_path, _slug(idea))
            if url:
                (out_dir / "url.txt").write_text(url)

        size_kb = game_path.stat().st_size // 1024
        lines   = game_path.read_text(encoding="utf-8", errors="ignore").count("\n")

        if url:
            msg = (
                f"✅ <b>완성!</b>\n\n"
                f"💡 {html.escape(idea)}\n"
                f"📦 {lines}줄, {size_kb}KB\n\n"
                f"🌐 <b>{html.escape(url)}</b>"
            )
            send_html(chat_id, msg)
            # 그룹에서 작업한 경우 개인 DM에도 완료 알림
            if chat_id != AUTHORIZED_ID:
                send_html(AUTHORIZED_ID, f"🔔 게임 완료 알림\n\n{msg}")
        else:
            msg = (
                f"✅ <b>완성!</b>\n\n"
                f"💡 {html.escape(idea)}\n"
                f"📦 {lines}줄, {size_kb}KB\n\n"
                f"배포 링크를 받으려면 같은 아이디어를 다시 보내고 배포 여부를 '예'로 선택하세요."
            )
            send_html(chat_id, msg)
            # 그룹에서 작업한 경우 개인 DM에도 완료 알림
            if chat_id != AUTHORIZED_ID:
                send_html(AUTHORIZED_ID, f"🔔 게임 완료 알림\n\n{msg}")

        # 대화 히스토리 초기화 (새 아이디어 받을 준비)
        _clear_history(chat_id)

    except Exception as e:
        _log_error(f"forge_worker:{idea}", traceback.format_exc())
        send(chat_id, f"❌ 오류: {str(e)[:200]}")
    finally:
        with _active_lock:
            _active.pop(chat_id, None)

# ── 미완성 파이프라인 재개 ─────────────────────────────────────────────────
def _find_incomplete_pipelines() -> list[dict]:
    """game.html이 없고 pipeline_state.json이 있는 디렉토리를 찾는다."""
    if not OUTPUT_DIR.exists():
        return []
    result = []
    for d in sorted(OUTPUT_DIR.iterdir(), reverse=True)[:20]:
        if (d / "game.html").exists():
            continue
        state = load_state(str(d))
        if state and state.get("idea") and state.get("stage") not in ("done", "failed", None):
            result.append({"output_dir": str(d), "state": state})
    return result


def _handle_resume(chat_id: int):
    """미완성 파이프라인 목록을 보여주고 재개 여부를 묻는다."""
    incomplete = _find_incomplete_pipelines()
    if not incomplete:
        send(chat_id, "재개할 미완성 작업이 없습니다.")
        return

    lines = ["🔄 <b>미완성 작업 목록</b>\n재개할 번호를 입력하세요.\n"]
    _incomplete_list[chat_id] = incomplete
    for i, item in enumerate(incomplete, 1):
        state = item["state"]
        stage_labels = {
            "started": "기획 중", "designer": "설계 중",
            "sound_asset": "사운드/에셋 준비 중", "developer": "코드 작성 중",
        }
        stage = stage_labels.get(state.get("stage", ""), state.get("stage", "?"))
        idea = state.get("idea", "알 수 없음")[:40]
        ts = Path(item["output_dir"]).name
        lines.append(f"<b>{i}.</b> {html.escape(idea)}\n   📍 중단 위치: {stage} ({ts[:8]})")
    send_html(chat_id, "\n".join(lines))


# 재개 대기 목록 (chat_id별)
_incomplete_list: dict[int, list[dict]] = {}


# ── 게임 수정 워커 ─────────────────────────────────────────────────────────
def _modify_worker(chat_id: int, output_dir: str, changes: str, title: str):
    try:
        send(chat_id, f"🔧 <b>{html.escape(title)}</b> 수정 중...\n잠시만 기다려 주세요.")

        success = modifier_modify(output_dir, changes)

        with _active_lock:
            if _active.get(chat_id, {}).get("cancelled"):
                send(chat_id, "🚫 작업이 취소되었습니다.")
                return

        game_path = Path(output_dir) / "game.html"
        if not success or not game_path.exists():
            send(chat_id, "❌ 수정에 실패했어요. 다시 시도해 주세요.")
            return

        report_path = Path(output_dir) / "modify_report.md"
        report_text = ""
        if report_path.exists():
            # 변경 사항 요약만 추출
            raw = report_path.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"## 변경 사항\n([\s\S]+?)(?=##|$)", raw)
            if m:
                report_text = "\n" + m.group(1).strip()[:300]

        size_kb = game_path.stat().st_size // 1024
        send_html(chat_id,
            f"✅ <b>수정 완료!</b>\n\n"
            f"🎮 {html.escape(title)}\n"
            f"📦 {size_kb}KB{html.escape(report_text) if report_text else ''}"
        )

        # 수정 모드 유지 (같은 게임 계속 수정 가능)
        _clear_history(chat_id)
        with _modify_target_lock:
            target = _modify_target.get(chat_id)
        if target:
            send_html(chat_id,
                f"계속 수정하려면 원하는 내용을 말씀해 주세요.\n"
                f"다른 게임을 선택하려면 /games 를 입력하세요."
            )

    except Exception as e:
        _log_error(f"modify_worker:{title}", traceback.format_exc())
        send(chat_id, f"❌ 수정 오류: {str(e)[:200]}")
    finally:
        with _active_lock:
            _active.pop(chat_id, None)


# ── 메시지 핸들러 ──────────────────────────────────────────────────────────
def _handle(msg: dict):
    chat_id   = msg.get("chat", {}).get("id", 0)
    chat_type = msg.get("chat", {}).get("type", "private")
    user_id   = msg.get("from", {}).get("id", 0)
    text      = (msg.get("text") or "").strip()

    # 그룹/슈퍼그룹: 인증된 사용자는 멘션 없이도 반응, 타인은 멘션 필수
    is_group = chat_type in ("group", "supergroup")
    if is_group:
        mention = f"@{BOT_USERNAME}"
        has_mention = mention.lower() in text.lower()
        if not has_mention and user_id != AUTHORIZED_ID:
            return  # 타인이 멘션 없이 보낸 메시지는 무시
        # 멘션 텍스트 제거 후 처리
        if has_mention:
            text = re.sub(re.escape(mention), "", text, flags=re.IGNORECASE).strip()
        if not text:
            text = "/start"

    if user_id != AUTHORIZED_ID:
        send(chat_id, "⛔ 권한 없음")
        return
    if not text:
        return

    # ── 명령어 ──
    if text in ("/start", "/start@sol_kzvza1_bot"):
        _clear_history(chat_id)
        send_html(chat_id,
            "🎮 <b>Game Forge</b>\n\n"
            "어떤 게임을 만들고 싶으세요?\n"
            "아이디어를 자유롭게 말씀해 주세요.\n\n"
            "예: <i>적을 피하는 우주선 게임</i>\n"
            "    <i>블록을 쌓는 퍼즐 게임</i>"
        )
        return

    if text == "/cancel":
        with _active_lock:
            job = _active.get(chat_id)
            if job:
                job["cancelled"] = True
                send(chat_id, "🚫 취소 요청됨. 현재 단계가 끝나면 중단됩니다.")
                _clear_history(chat_id)
            else:
                send(chat_id, "취소할 작업이 없습니다.")
        return

    if text == "/resume":
        _handle_resume(chat_id)
        return

    if text == "/games":
        if not OUTPUT_DIR.exists():
            send(chat_id, "아직 만들어진 게임이 없습니다.")
            return
        games = [g for g in sorted(OUTPUT_DIR.iterdir(), reverse=True)
                 if (g / "game.html").exists()][:8]
        if not games:
            send(chat_id, "완성된 게임이 없습니다.")
            return

        # 게임 목록을 번호로 저장 (수정 선택용)
        _games_list[chat_id] = []
        lines = ["🎮 <b>게임 목록</b>\n수정할 게임 번호를 입력하세요.\n"]
        for i, g in enumerate(games, 1):
            game_html = g / "game.html"
            url_file  = g / "url.txt"
            url = url_file.read_text().strip() if url_file.exists() else ""
            gdd_text = (g / "gdd.md").read_text(encoding="utf-8", errors="ignore") if (g / "gdd.md").exists() else ""
            title_m  = re.search(r"게임 제목.*?\n(.+)", gdd_text)
            title    = title_m.group(1).strip()[:30] if title_m else g.name
            size_kb  = game_html.stat().st_size // 1024
            _games_list[chat_id].append({"output_dir": str(g), "title": title})
            url_line = f"\n  🌐 {html.escape(url)}" if url else ""
            lines.append(f"<b>{i}.</b> {html.escape(title)} ({size_kb}KB){url_line}")
        send_html(chat_id, "\n".join(lines))
        return

    # 재개 번호 선택 → 파이프라인 재개
    if chat_id in _incomplete_list and text.strip().isdigit():
        idx = int(text.strip()) - 1
        items = _incomplete_list.get(chat_id, [])
        if 0 <= idx < len(items):
            item = items[idx]
            del _incomplete_list[chat_id]
            state = item["state"]
            out_dir = Path(item["output_dir"])

            send_html(chat_id,
                f"🔄 <b>재개합니다!</b>\n"
                f"💡 {html.escape(state.get('idea', ''))}\n"
                f"잠시만 기다려 주세요..."
            )

            forge_args = {
                "idea":       state.get("idea", ""),
                "style":      state.get("style", "pixel"),
                "engine":     state.get("engine", "vanilla"),
                "assets":     state.get("use_assets", False),
                "assets_url": state.get("itchio_url",
                              "https://itch.io/game-assets/free/tag-2d/tag-pixel-art"),
                "skip_qa":    state.get("skip_qa", False),
                "max_retries": state.get("max_retries", 2),
                "deploy":     False,
            }
            t = threading.Thread(
                target=_forge_worker,
                args=(chat_id, forge_args, out_dir),
                daemon=True,
            )
            with _active_lock:
                _active[chat_id] = {
                    "idea":      forge_args["idea"],
                    "out_dir":   out_dir,
                    "thread":    t,
                    "cancelled": False,
                }
            t.start()
            return
        else:
            send(chat_id, f"1~{len(items)} 사이의 번호를 입력해 주세요.")
            return

    # 게임 번호 선택 → 수정 모드 진입
    if chat_id in _games_list and text.strip().isdigit():
        idx = int(text.strip()) - 1
        games = _games_list.get(chat_id, [])
        if 0 <= idx < len(games):
            target = games[idx]
            with _modify_target_lock:
                _modify_target[chat_id] = target
            del _games_list[chat_id]
            _clear_history(chat_id)
            send_html(chat_id,
                f"🔧 <b>{html.escape(target['title'])}</b> 수정 모드\n\n"
                f"어떻게 수정할까요? 자유롭게 말씀해 주세요.\n"
                f"예: <i>플레이어 속도 좀 줄여줘</i>\n"
                f"    <i>적 색깔을 빨간색으로 바꿔줘</i>\n"
                f"    <i>점프력 높여줘</i>\n\n"
                f"수정 모드 종료: /start"
            )
            return
        else:
            send(chat_id, f"1~{len(games)} 사이의 번호를 입력해 주세요.")
            return

    # ── 제작/수정 중이면 대기 안내 ──
    with _active_lock:
        if chat_id in _active:
            send(chat_id, "⏳ 지금 게임 제작/수정 중이에요. /cancel 로 취소 가능합니다.")
            return

    # 수정 모드 컨텍스트 주입 — Claude가 어떤 게임을 수정해야 하는지 알 수 있게 한다
    with _modify_target_lock:
        mt = _modify_target.get(chat_id)

    effective_text = text
    if mt:
        effective_text = (
            f"[수정 모드] 게임: {mt['title']}\n"
            f"경로: {mt['output_dir']}\n\n"
            f"{text}"
        )

    # ── Claude 대화 ──
    # 수신 즉시 "typing..." 표시 — API 응답 대기 중임을 알려줌
    _api("sendChatAction", chat_id=chat_id, action="typing")
    response = _chat(chat_id, effective_text)

    # FORGE / READY / MODIFY 블록 감지
    forge_args  = _extract_forge(response)
    ready_spec  = _extract_ready(response)
    modify_args = _extract_modify(response)
    display     = _strip_code_blocks(response)

    # 대화 응답 전송
    if display:
        send(chat_id, display)

    # READY 블록 → 제작 명세 카드 표시 (확인 대기)
    if ready_spec and ready_spec.get("idea") and not forge_args:
        send_html(chat_id, _ready_card(ready_spec))
        return  # FORGE 블록이 올 때까지 대기

    # 제작 시작 (사용자 확인 후 Claude가 FORGE 블록 출력한 경우)
    if forge_args and forge_args.get("idea"):
        ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = OUTPUT_DIR / ts

        t = threading.Thread(
            target=_forge_worker,
            args=(chat_id, forge_args, out_dir),
            daemon=True,
        )
        with _active_lock:
            _active[chat_id] = {
                "idea":      forge_args["idea"],
                "out_dir":   out_dir,
                "thread":    t,
                "cancelled": False,
            }
        t.start()
        return

    # 수정 시작 (Claude가 MODIFY 블록 출력한 경우)
    if modify_args and modify_args.get("output_dir") and modify_args.get("changes"):
        mod_dir = modify_args["output_dir"]
        changes = modify_args["changes"]
        with _modify_target_lock:
            cur = _modify_target.get(chat_id)
        title = cur["title"] if cur else Path(mod_dir).name

        t = threading.Thread(
            target=_modify_worker,
            args=(chat_id, mod_dir, changes, title),
            daemon=True,
        )
        with _active_lock:
            _active[chat_id] = {
                "idea":      title,
                "out_dir":   Path(mod_dir),
                "thread":    t,
                "cancelled": False,
            }
        t.start()

# ── 폴링 루프 ──────────────────────────────────────────────────────────────
def _get_offset() -> int:
    try:
        return int(OFFSET_FILE.read_text().strip())
    except Exception:
        return 0

def _save_offset(offset: int):
    OFFSET_FILE.write_text(str(offset))

def _notify_incomplete_on_start():
    """봇 시작 시 미완성 파이프라인이 있으면 사용자에게 알린다."""
    if not AUTHORIZED_ID:
        return
    try:
        incomplete = _find_incomplete_pipelines()
        if incomplete:
            lines = [f"🔄 봇이 재시작됐어요. 미완성 작업 {len(incomplete)}개가 있습니다.\n"]
            for item in incomplete:
                idea = item["state"].get("idea", "?")[:40]
                lines.append(f"• {html.escape(idea)}")
            lines.append("\n/resume 로 재개할 수 있습니다.")
            send_html(AUTHORIZED_ID, "\n".join(lines))
    except Exception:
        pass


def poll():
    print(f"🎮 Game Forge Bot 시작 (authorized: {AUTHORIZED_ID})", flush=True)
    _notify_incomplete_on_start()
    offset = _get_offset()
    while True:
        try:
            res = _api("getUpdates", offset=offset, timeout=30,
                       allowed_updates=["message"])
            for update in res.get("result", []):
                offset = update["update_id"] + 1
                _save_offset(offset)
                msg = update.get("message")
                if msg:
                    # 메시지 처리를 별도 쓰레드에서 실행 — 폴링 루프 블로킹 방지
                    threading.Thread(
                        target=_safe_handle,
                        args=(msg,),
                        daemon=True,
                    ).start()
        except Exception as e:
            _log_error("poll", str(e))
            time.sleep(5)

def _safe_handle(msg: dict):
    try:
        _handle(msg)
    except Exception:
        _log_error("handle", traceback.format_exc())

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN 없음")
        sys.exit(1)
    poll()
