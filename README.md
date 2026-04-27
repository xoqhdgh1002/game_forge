# 🎮 Game Forge

아이디어 한 줄 → 브라우저에서 바로 실행되는 HTML5 게임 자동 생성 시스템.

텔레그램 봇으로 대화하면 AI 에이전트 팀이 자동으로 게임을 만들어줍니다.

---

## 데모

```
사용자: 무한 점프 게임, 장애물 피하기, 귀여운 캐릭터
봇: 게임 스타일을 골라주세요 — 픽셀 / 미니멀 / 레트로
사용자: 픽셀
봇: 🎮 제작 시작합니다...
    [10분 후]
봇: ✅ 완성! 460줄, 38KB
```

---

## 아키텍처

```
사용자 메시지
    ↓
[bot.py] Telegram 봇 — 대화 수집 & 오케스트레이터 호출
    ↓
[orchestrator.py] 파이프라인 총지휘
    ↓
[Producer]  아이디어 → 게임 디자인 문서 (GDD)
    ↓
[Designer]  GDD → 세부 설계 (조작/레벨/적 패턴/UI)
    ↓
[Sound] ──┐  ← Designer 완료 후 병렬 실행
[Asset] ──┘
    ↓
[Developer] 설계 + 에셋 → HTML5 단일 파일
    ↓
[QA]        코드 검토 → 버그 수정 반영
    ↓
game.html  (브라우저 즉시 실행)
```

---

## 설치

### 요구사항

- Python 3.12+
- `claude_agent_sdk` (Anthropic Agent SDK)
- Telegram Bot Token

### 환경 설정

```bash
cp bridge.env.example bridge.env
# bridge.env 편집:
# TELEGRAM_BOT_TOKEN=your_token
# TELEGRAM_USER_ID=your_user_id
# ANTHROPIC_API_KEY=your_api_key
```

### 의존성 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install anthropic python-dotenv
```

---

## 실행

### 텔레그램 봇

```bash
# 직접 실행
python3 bot.py

# 백그라운드 (pm2)
pm2 start bot.py --name game-forge --interpreter python3
```

### CLI (봇 없이 직접)

```bash
python3 forge.py "무한 점프 게임"
python3 forge.py "우주 슈팅게임" --style retro
python3 forge.py "퍼즐 게임" --engine phaser --skip-qa
```

---

## 봇 명령어

| 명령어 | 설명 |
|--------|------|
| `/start` | 시작 / 새 게임 아이디어 입력 |
| `/games` | 지금까지 만든 게임 목록 |
| `/cancel` | 진행 중인 작업 취소 |

게임 목록에서 번호를 입력하면 수정 모드로 전환됩니다.

---

## 출력 구조

```
output/
└── 20260427_153000/
    ├── game.html          # 완성된 게임 (즉시 실행)
    ├── gdd.md             # 게임 디자인 문서
    ├── design.md          # 세부 설계서
    ├── qa_report.md       # QA 검토 결과
    ├── sounds.json        # 사운드 설정
    └── pipeline_state.json  # 파이프라인 복구용 상태
```

---

## 에이전트 구성

| 에이전트 | 파일 | 역할 |
|---------|------|------|
| Producer | `agents/producer.py` | 아이디어 → GDD 초안 |
| Designer | `agents/designer.py` | GDD → 세부 설계 |
| Developer | `agents/developer.py` | 설계 → HTML5 코드 |
| QA | `agents/qa.py` | 코드 검토 & 버그 수정 |
| Sound | `agents/sound_agent.py` | 사운드 효과 설계 |
| Asset Collector | `agents/asset_collector.py` | 무료 에셋 수집 |
| Modifier | `agents/modifier.py` | 기존 게임 수정 |
| Notify | `agents/notify.py` | 텔레그램 진행 알림 |

---

## 주요 특징

- **단일 파일 출력** — `game.html` 하나로 어디서든 실행
- **GAN 루프** — Generator(Developer) + Evaluator(QA) 반복으로 품질 향상
- **파이프라인 복구** — 중단돼도 `pipeline_state.json`으로 이어서 재실행
- **실시간 알림** — 각 단계 완료 시 텔레그램으로 진행 상황 전송
- **수정 모드** — 완성된 게임을 대화로 수정 가능

---

## 라이선스

MIT
