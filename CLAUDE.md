# Game Forge — AI 에이전트 게임 개발 팀

개인 도구. 아이디어 한 줄 → HTML5 게임 자동 생성 시스템.

---

## 팀 구성

| 에이전트 | 역할 | 담당 |
|---------|------|------|
| Producer | 아이디어 → 게임 명세 분해 | `forge.py` 오케스트레이터 |
| Designer | 게임 디자인 문서 작성 | GDD (장르/조작/규칙/비주얼) |
| Developer | HTML5 게임 코드 작성 | 단일 HTML 파일 출력 |
| QA | 코드 검토 + 개선 제안 | 오류 탐지, 플레이어블 확인 |

---

## 디렉토리 구조

```
game_forge/
├── CLAUDE.md          # 이 파일
├── forge.py           # 메인 오케스트레이터 (CLI 진입점)
├── agents/
│   ├── producer.py    # 아이디어 → GDD
│   ├── designer.py    # GDD → 세부 설계
│   ├── developer.py   # 설계 → HTML5 코드
│   └── qa.py          # 코드 → 검토 + 수정본
├── templates/
│   └── base.html      # 게임 기본 HTML 틀
└── output/            # 생성된 게임들 (YYYYMMDD_HHMMSS/)
    └── YYYYMMDD_HHMMSS/
        ├── game.html
        ├── gdd.md
        └── qa_report.md
```

---

## 사용법

```bash
# 기본 실행
python3 forge.py "무한 점프 게임, 장애물 피하기"

# 옵션
python3 forge.py "아이디어" --style retro     # 비주얼 스타일
python3 forge.py "아이디어" --skip-qa         # QA 단계 생략
python3 forge.py "아이디어" --engine phaser   # Phaser.js 사용 (기본: vanilla)
```

---

## 출력

- `output/YYYYMMDD_HHMMSS/game.html` — 브라우저에서 바로 실행 가능
- `output/YYYYMMDD_HHMMSS/gdd.md` — 게임 디자인 문서
- `output/YYYYMMDD_HHMMSS/qa_report.md` — QA 검토 결과

---

## 에이전트 파이프라인

```
사용자 입력
    ↓
[Producer] 아이디어 분석 → GDD 초안 (장르/메카닉/승리조건/비주얼)
    ↓
[Designer] GDD 구체화 → 세부 설계 (조작키/레벨구조/적 패턴/UI)
    ↓
[Developer] 설계 → 완전한 HTML5 코드 (단일 파일, 즉시 실행)
    ↓
[QA] 코드 검토 → 버그 리포트 + 수정본 반영
    ↓
최종 game.html 출력
```
