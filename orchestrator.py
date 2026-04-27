"""
Orchestrator v4 — Python 직접 파이프라인 제어

LLM이 bash 명령 순서를 판단하던 방식을 제거하고,
Python subprocess 로 각 에이전트 CLI를 직접 호출한다.

파이프라인:
  Producer → Designer → [Sound + Asset(병렬)] → Developer → QA → BrowserQA
"""
import asyncio
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

PYTHON     = str(Path(sys.executable))
AGENTS_DIR = Path(__file__).parent / "agents"


# ── 유틸 ──────────────────────────────────────────────────────────────────────

def _ts() -> str:
    return datetime.now().strftime("[%H:%M:%S]")


def _log(msg: str):
    print(f"{_ts()} {msg}", flush=True)


def _save_state(output_dir: str, state: dict):
    try:
        p = Path(output_dir) / "pipeline_state.json"
        state["updated_at"] = datetime.now().isoformat()
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_state(output_dir: str) -> dict | None:
    try:
        p = Path(output_dir) / "pipeline_state.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def _run(cmd: list[str], label: str, output_dir: str) -> tuple[int, str]:
    """subprocess 실행 후 (returncode, stdout+stderr) 반환."""
    _log(f"▶ [{label}] 시작...")
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=output_dir,
            timeout=600,
        )
        out = (r.stdout + r.stderr).strip()
        if r.returncode == 0:
            _log(f"✅ [{label}] 완료")
        else:
            _log(f"❌ [{label}] 실패 (exit {r.returncode}): {out[:200]}")
        return r.returncode, out
    except subprocess.TimeoutExpired:
        _log(f"⏰ [{label}] 타임아웃 (600s)")
        return 1, "timeout"
    except Exception as e:
        _log(f"💥 [{label}] 예외: {e}")
        return 1, str(e)


def _notify(output_dir: str, msg: str):
    """텔레그램 알림 — 실패해도 파이프라인 중단 없음."""
    try:
        subprocess.run(
            [PYTHON, str(AGENTS_DIR / "notify.py"), output_dir, msg],
            timeout=10, capture_output=True,
        )
    except Exception:
        pass


# ── 파이프라인 단계 ───────────────────────────────────────────────────────────

def _phase1_producer(idea: str, style: str, engine: str, output_dir: str) -> bool:
    cmd = [PYTHON, str(AGENTS_DIR / "run_producer.py"), idea, style, engine, output_dir]
    code, _ = _run(cmd, "Producer", output_dir)
    if code != 0:
        _log("↩ Producer 재시도...")
        code, _ = _run(cmd, "Producer(retry)", output_dir)
    return code == 0


def _phase2a_designer(output_dir: str) -> bool:
    cmd = [PYTHON, str(AGENTS_DIR / "run_designer.py"), output_dir]
    code, _ = _run(cmd, "Designer", output_dir)
    if code != 0:
        _log("↩ Designer 재시도...")
        code, _ = _run(cmd, "Designer(retry)", output_dir)
    return code == 0


def _phase2b_parallel(output_dir: str, use_assets: bool, itchio_url: str):
    """Sound + Asset 병렬 실행 (ThreadPoolExecutor)."""
    def run_sound():
        return _run(
            [PYTHON, str(AGENTS_DIR / "run_sound_agent.py"), output_dir],
            "Sound", output_dir,
        )

    def run_asset():
        return _run(
            [PYTHON, str(AGENTS_DIR / "run_asset_collector.py"), output_dir, itchio_url],
            "Asset", output_dir,
        )

    tasks = [run_sound]
    if use_assets:
        tasks.append(run_asset)

    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(lambda f: f(), tasks))


def _phase3_dev_qa(
    output_dir: str,
    engine: str,
    skip_qa: bool,
    max_retries: int,
) -> bool:
    """Developer → QA 루프. True=game.html 존재."""
    for attempt in range(1, max_retries + 1):
        _notify(output_dir, f"⚙️ 코드 작성 중... ({attempt}/{max_retries})")
        dev_cmd = [PYTHON, str(AGENTS_DIR / "run_developer.py"), output_dir, engine]
        code, _ = _run(dev_cmd, f"Developer({attempt})", output_dir)
        if code != 0:
            if attempt < max_retries:
                continue
            _log("Developer 최종 실패 — game.html 없이 종료")
            return False

        if skip_qa:
            _log("⏭ QA 건너뜀")
            return True

        qa_cmd = [PYTHON, str(AGENTS_DIR / "run_qa.py"), output_dir]
        qa_code, _ = _run(qa_cmd, f"QA({attempt})", output_dir)

        if qa_code == 0:
            _notify(output_dir, "🔍 QA 통과! 브라우저 검증 중...")
            return True
        elif qa_code == 2:
            remaining = max_retries - attempt
            if remaining > 0:
                _notify(output_dir, f"🔧 버그 수정 중... ({remaining}회 남음)")
            # 다음 iteration에서 Developer 재실행
        else:
            # QA 자체 오류 — game.html은 있으므로 그냥 통과
            _log("QA 오류 (exit 1) — game.html 그대로 사용")
            return True

    _log("max_retries 초과 — 현재 game.html 그대로 사용")
    return (Path(output_dir) / "game.html").exists()


def _phase4_browser_qa(output_dir: str) -> dict:
    """Playwright 헤드리스 브라우저로 실제 실행 검증."""
    browser_qa = AGENTS_DIR / "browser_qa.py"
    if not browser_qa.exists():
        return {"skipped": True}
    code, out = _run(
        [PYTHON, str(browser_qa), output_dir],
        "BrowserQA", output_dir,
    )
    return {"passed": code == 0, "output": out}


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────

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
    게임 파이프라인을 Python이 직접 제어하여 실행한다.
    Returns: True(game.html 생성 성공) / False(실패)
    """
    _save_state(output_dir, {
        "stage": "started", "idea": idea, "style": style, "engine": engine,
        "use_assets": use_assets, "skip_qa": skip_qa, "max_retries": max_retries,
    })

    # Phase 1 — 기획
    _notify(output_dir, "📝 기획 시작...")
    if not _phase1_producer(idea, style, engine, output_dir):
        _log("❌ 오케스트레이션 실패 — Producer 중단")
        _save_state(output_dir, {"stage": "failed", "reason": "producer"})
        return False
    _save_state(output_dir, {"stage": "designer", "idea": idea})
    _notify(output_dir, "✅ 기획 완료! 설계 중...")

    # Phase 2a — 설계
    _phase2a_designer(output_dir)   # 실패해도 진행 (GDD만으로도 개발 가능)
    _save_state(output_dir, {"stage": "sound_asset", "idea": idea})
    _notify(output_dir, "🎨 설계 완료! 사운드·에셋 준비 중...")

    # Phase 2b — Sound + Asset 병렬
    _phase2b_parallel(output_dir, use_assets, itchio_url)
    _save_state(output_dir, {"stage": "developer", "idea": idea})
    _notify(output_dir, "🔊 준비 완료! 코드 작성 시작...")

    # Phase 3 — 개발 + QA 루프
    success = _phase3_dev_qa(output_dir, engine, skip_qa, max_retries)

    if not success:
        _log("❌ 오케스트레이션 실패")
        _save_state(output_dir, {"stage": "failed", "reason": "developer"})
        return False

    # Phase 4 — 브라우저 실행 검증
    browser_result = _phase4_browser_qa(output_dir)
    if not browser_result.get("skipped"):
        if browser_result.get("passed"):
            _notify(output_dir, "🌐 브라우저 검증 통과!")
        else:
            _notify(output_dir, "⚠️ 브라우저 검증 실패 — 게임은 생성됨")

    game_html = Path(output_dir) / "game.html"
    final_success = game_html.exists() and game_html.stat().st_size > 500
    _save_state(output_dir, {"stage": "done" if final_success else "failed", "idea": idea})

    if final_success:
        _log(f"✅ 오케스트레이션 완료: {game_html}")
    else:
        _log("❌ 오케스트레이션 실패")

    return final_success
