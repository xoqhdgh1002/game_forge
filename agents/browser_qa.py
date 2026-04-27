#!/usr/bin/env python3
"""
Browser QA — Playwright 헤드리스 브라우저로 game.html 실행 검증

검사 항목:
  1. 페이지 로드 (JS 크래시 없음)
  2. <canvas> 렌더링 확인
  3. JS 콘솔 에러 수집
  4. 3초 후에도 캔버스가 살아있는지 확인

exit 0: 통과 (치명적 JS 오류 없음, canvas 존재)
exit 1: 실패 (페이지 로드 불가 또는 canvas 없음)
exit 2: 경고 (JS 오류 있음 — 게임은 동작할 수 있음)
"""
import json
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, Error as PlaywrightError
except ImportError:
    print("SKIP: playwright 미설치", flush=True)
    sys.exit(0)


def run(output_dir: str) -> int:
    game_path = Path(output_dir) / "game.html"
    report_path = Path(output_dir) / "browser_qa_report.md"

    if not game_path.exists():
        print(f"ERROR: {game_path} 없음", file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    canvas_found = False
    load_ok = False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # JS 콘솔 에러 수집
            def on_console(msg):
                if msg.type == "error":
                    errors.append(msg.text)
                elif msg.type == "warning":
                    warnings.append(msg.text)

            page.on("console", on_console)

            # 페이지 이동 오류 수집
            page_errors: list[str] = []
            page.on("pageerror", lambda e: page_errors.append(str(e)))

            # 로드
            try:
                page.goto(f"file://{game_path.resolve()}", timeout=15000)
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                load_ok = True
            except PlaywrightError as e:
                errors.append(f"페이지 로드 실패: {e}")
                browser.close()
                _write_report(report_path, errors, warnings, False, False)
                return 1

            # 3초 대기 (게임 루프 시작 확인)
            page.wait_for_timeout(3000)

            # canvas 존재 여부
            canvas_found = page.query_selector("canvas") is not None

            # pageerror 병합
            errors.extend(page_errors)

            browser.close()

    except Exception as e:
        errors.append(f"Playwright 예외: {e}")
        _write_report(report_path, errors, warnings, load_ok, canvas_found)
        return 1

    _write_report(report_path, errors, warnings, load_ok, canvas_found)

    # 결과 출력
    if not canvas_found:
        print("FAIL: <canvas> 없음 — 게임이 렌더링되지 않습니다.")
        return 1

    if errors:
        print(f"WARN: JS 오류 {len(errors)}개 발견")
        for e in errors[:3]:
            print(f"  - {e[:120]}")
        return 2

    print(f"OK: canvas 확인, JS 오류 없음 (경고 {len(warnings)}개)")
    return 0


def _write_report(path: Path, errors: list, warnings: list, load_ok: bool, canvas: bool):
    lines = [
        "# Browser QA 리포트\n",
        f"- 페이지 로드: {'✅' if load_ok else '❌'}",
        f"- Canvas 렌더링: {'✅' if canvas else '❌'}",
        f"- JS 오류: {len(errors)}개",
        f"- JS 경고: {len(warnings)}개",
    ]
    if errors:
        lines.append("\n## JS 오류")
        for e in errors:
            lines.append(f"- `{e}`")
    if warnings:
        lines.append("\n## JS 경고")
        for w in warnings[:5]:
            lines.append(f"- `{w}`")
    try:
        path.write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(run(out_dir))
