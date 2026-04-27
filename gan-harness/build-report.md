# GAN Harness Build Report

**Brief:** 사마천의 사기(史記) 기반 2D 픽셀 RPG — 아이들이 역사 인물(항우, 유방, 형가 등)을 만나며 중국 역사를 배우는 탐험 게임
**Result:** ✅ PASS
**Iterations:** 1 / 2
**Final Score:** 8.10 / 10.0

---

## Score Progression

| Iter | Design | Originality | Craft | Functionality | Total |
|------|--------|-------------|-------|---------------|-------|
| 1    | 2.0/2.5 | 1.0/1.5 | 1.55/2.0 | 3.55/4.0 | **8.10** |

---

## Game Title
**시기열전 (Shiji Yeoljeon) — 사마천의 발자취**

A top-down 2D pixel-art RPG where a young scribe-apprentice explores ancient China, meets 3 Shiji figures (형가, 항우, 유방), collects 죽간 (bamboo slips), and learns history through dialogue and choices.

---

## What Was Built
- Single self-contained HTML file (~62KB, 2407 lines)
- Vanilla JS + HTML5 Canvas (960×540, scales to window)
- State machine: TITLE → CHAPTER_CARD → PLAYING → DIALOGUE → INVENTORY → GLOSSARY → TRANSITION → WIN
- Top-down movement with WASD/arrow keys, per-axis collision + wall sliding
- 3 historical NPC scenes: 형가 (易水), 항우 (거록), 유방 (함양)
- Dialogue system with typewriter effect, branching choices, and lesson-tied questions
- 죽간 collection system with scroll-wall display in hub
- Hanji parchment palette, programmatic pixel art (all ctx.fillRect, no external images)
- Web Audio API — procedural pentatonic 가야금 plucks
- Chapter card transitions with vertical hanja display

---

## Remaining Issues

### High (should fix)
1. Title menu navigation bug — `up` key increments instead of decrements
2. "처음부터 다시" doesn't clear progress (should call `game.collected.clear()`)
3. Mini-games are dialogue-choice nodes, not standalone mini-game screens
4. Player and 형가 sprites are visually too similar for young children
5. Hub scroll-wall is a small placard, not a full scroll-wall as specified

### Medium (nice to fix)
1. Glossary mirrors inventory content — should have its own `meaning` field per idiom
2. No pause menu (Esc closes overlays only)
3. No save/load persistence (only mute persists)
4. Walk cycle foot positions differ by only 1px — needs more contrast
5. Win screen triggered by setTimeout, not by 사마천 final dialogue

---

## Hard-Fail Conditions Check
- ✅ Canvas renders on load (no blank screen)
- ✅ Movement works (WASD/arrow keys → per-axis collision)
- ✅ No server required (file:// compatible)
- ✅ No JS syntax errors
- ✅ No external image files (all programmatic pixel art)

---

## Anti-Pattern Deductions
None — game passes all anti-slop checks:
- No rainbow gradient on title ✅
- No emoji as icons ✅
- No black background (uses parchment #F4E8C8) ✅
- No on-screen violence ✅
- Editorial asymmetric HUD ✅

---

## Files Created
- `gan-harness/spec.md` — full product specification (Planner)
- `gan-harness/eval-rubric.md` — 10-point weighted rubric (Planner)
- `gan-harness/game.html` — final playable game (Generator iter 1)
- `gan-harness/generator-state.md` — generator notes on deferred items
- `gan-harness/feedback/feedback-001.md` — full evaluation (Evaluator iter 1)
- `gan-harness/build-report.md` — this file
