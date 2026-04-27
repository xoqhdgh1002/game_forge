#!/usr/bin/env python3
"""
Telegram Notifier — 오케스트레이터가 Bash로 호출하는 진행 알림 스크립트

사용법:
  python3 notify.py <output_dir> <message>

  output_dir 안의 chat_id.txt를 읽어 해당 chat_id로 메시지를 전송한다.
  chat_id.txt가 없으면 조용히 종료 (알림 실패는 파이프라인을 멈추지 않는다).
"""
import json
import sys
import urllib.request
from pathlib import Path


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


def notify(output_dir: str, message: str) -> bool:
    """텔레그램으로 진행 메시지를 전송한다. 실패해도 False만 반환."""
    out_path = Path(output_dir)
    chat_id_file = out_path / "chat_id.txt"

    if not chat_id_file.exists():
        return False

    chat_id = chat_id_file.read_text().strip()
    if not chat_id:
        return False

    env_file = Path(__file__).parent.parent / "bridge.env"
    cfg = _load_env(env_file)
    token = cfg.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": int(chat_id), "text": message}).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: notify.py <output_dir> <message>", file=sys.stderr)
        sys.exit(0)

    output_dir = sys.argv[1]
    message    = " ".join(sys.argv[2:])
    notify(output_dir, message)
    # 항상 exit 0 — 알림 실패는 파이프라인을 멈추지 않는다
