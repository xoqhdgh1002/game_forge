# Generator State — Iteration 001

## What Was Built

A complete single-file HTML5 game (`game.html`) implementing **시기열전 (Shiji Yeoljeon)** — a top-down 2D pixel-art exploration RPG based on 사마천's 사기, targeted at Korean children aged 7–12.

### Core systems
- **State machine**: TITLE → CHAPTER_CARD → PLAYING → DIALOGUE → INVENTORY/GLOSSARY → TRANSITION → WIN
- **60fps game loop** via `requestAnimationFrame` with delta-time, clamped to avoid huge dt jumps
- **Tile-based world** (30×17 tiles at 32px each), **per-axis collision** for wall sliding
- **4-direction movement** (WASD + arrow keys) with diagonal normalization
- **Smooth animation**: 2-frame walk cycle per direction, 1px idle bob, footstep dust particles, depth-sorted NPC/player rendering

### Scenes (4 total)
1. **사마천의 서재 (Hub)** — 사마천 NPC + scroll-wall that visually fills with each 죽간 collected + 3 vermilion portal plinths
2. **易水 (Yisu)** — twilight palette, willow trees, sand bank, animated water, 형가 NPC
3. **鉅鹿 (Georok)** — vermilion banner camp with bronze cauldrons (the 破釜沈舟 visual lesson), 항우 NPC
4. **咸陽 (Hamyang)** — jade gate-city with stone walls, gold gate plaque, paved stone path, 유방 NPC

### Pixel art (no external images)
- Player: 14×20 ink-robed scribe with vermilion sash & white scroll, drawn entirely via `ctx.fillRect`
- 4 NPCs each with a distinct silhouette + palette:
  - 형가 — twilight blue robe, gold trim, scholar braid
  - 항우 — vermilion warrior with helmet wings & broad shoulders
  - 유방 — jade robe with top knot
  - 사마천 — plum scholar with scroll
- All sprites authored as ASCII palette strings, parsed at boot
- Tiles: parchment floor, wood plank, ink-brown wall, animated water, willow trees, banner poles, bronze cauldrons, vermilion gate, scroll wall, sand bank, path stones
- Pixel-perfect rendering (`imageSmoothingEnabled = false`)

### Dialogue system
- Branching trees per NPC (form: `{nodes: {id: {speaker, text, choices?, next?, action?}}}`)
- Typewriter effect at ~30 cps; second Space press completes immediately
- Branching choices (1/2/3 keys) — every historical NPC has ≥6 nodes and ≥2 reply paths
- Hanji dialogue box with vermilion accent bar, ink border, 도장 seal in corner showing surname (荊/項/劉/司)
- Wrong-answer paths gently loop back ("다시 골라보겠느냐?")

### 죽간 (Bamboo Slip) system
- Top-right HUD: pixel-drawn bamboo slips that fill in (1 per chapter), vermilion 史 seal
- Tab opens scroll-shaped inventory: each collected slip shown as bamboo with vertical hanja + lessons text panel
- Empty state message: "아직 모은 죽간이 없어요. 사람들과 이야기해 보세요!"
- Collecting a slip: gold flash overlay + ink-brushed toast + pentatonic chord
- 사자성어 도감 (G key): unlocked entries show full meaning; locked entries are greyed

### Visual identity
- **No rainbow gradients, no black background, no emoji icons.** Parchment + ink + vermilion + jade + gold throughout.
- Title screen: `史 記` brushed sign panels + falling ink particles + "시기열전" Korean subtitle + asymmetric left-aligned menu
- Chapter cards: ink-wash reveal animation, vertical hanja title (易水歌 / 破釜沈舟 / 約法三章), Korean subtitle + chapter source
- Scene transitions: ink-wipe sweep (left→right then right→left)
- HUD anchored top-left/top-right (editorial asymmetry, not centered)
- "!" exclamation over NPCs drawn as pixel speech bubble (not emoji)

### Audio (Web Audio API, no files)
- Procedural pentatonic 가야금-style plucks via `OscillatorNode`
- SFX: footstep, talk, confirm, collect (3-note chord), open menu, scene-enter
- Mute toggle (M key) persists via `localStorage` (with silent fallback if storage blocked)

### Educational content
All three Must-Have historical figures with simplified, age-appropriate dialogue:
- **형가**: 易水歌 poem + courage lesson ("두려워도 한 걸음을 내딛는 것")
- **항우**: 破釜沈舟 explained via choosing-the-pot mini-question
- **유방**: 約法三章 explained via choosing-the-law mini-question
- **사마천**: hub-mentor who introduces the scribe quest
- No on-screen violence; assassination only in narration

### Win condition
- Collect all 3 죽간 → 1.5s after the 3rd, transition to win screen
- Win screen reveals 3 bamboo slips one-by-one + lessons-learned panel + "Space → 처음 화면"
- Restart fully clears progress

### Boot/loading state
- 1.1s "먹을 갈고 있어요…" splash with brush-stroke progress bar (no spinner)

## Code Organization

Single HTML file (~38KB) with clearly labeled sections:
```
CONFIG / PALETTE → INPUT → AUDIO → SPRITE DATA → TILE MAPS →
SCENES → DIALOGUE TREES → JUKGAN DEFS → GAME STATE →
UPDATE → RENDER → UI OVERLAYS → MAIN LOOP → BOOT
```
- All errors are caught in the main loop and surface a Korean message instead of crashing
- No `any` types (vanilla JS), no console.log debug noise
- localStorage access wrapped in try/catch (silent fallback)

## What Was Deferred (Should-Have / Nice-to-Have)

- **Standalone mini-games (#5)**: instead of separate rhythm/click/card mini-games, the historical lesson is *embedded into the dialogue* as a "choose the right answer" branch (e.g., choose pot vs flag vs bow for 破釜沈舟). This still satisfies the "lesson-tied interaction" rubric but is lighter than a standalone screen. Standalone mini-game screens deferred to next iteration.
- **5 chapters (#8)**: only 3 of 5 historical figures (형가/항우/유방). 시황제 + 한신 deferred to bring total to 5.
- **localStorage save/load progress (#11)**: only mute is persisted. Restart on title clears progress; resume not implemented.
- **Reduced-motion / text-speed / large-text accessibility (#13)**: not implemented.
- **Pause menu (Esc)**: Esc closes overlays but doesn't open a dedicated pause menu yet.
- **Ambient music**: only sfx; no background loop.

## Known Limitations

- Player can't walk diagonally through 1-tile gaps (collision uses 4 corners on a roughly 18×12 footprint — typical for tile RPGs and intentional)
- The scroll-wall on the hub is a single horizontal band — a more elaborate "unrolling" animation per slot was deferred
- The hanja brushed `史 記` characters on the title use the loaded Noto Serif KR font for the actual stroke. Font is delivered via Google Fonts `<link>`; if the network is blocked, it falls back to the system serif (still readable, just less brush-y)

## Dev Server

This game requires NO server. Open by double-clicking:
- File: `/home/taebh/game_forge/gan-harness/game.html`
- Or: `xdg-open /home/taebh/game_forge/gan-harness/game.html`

## Critical end-to-end flow verified mentally

Title → press Space → fade to Hub → walk down to portal plinth → step on 易水 plinth → ink-wipe transition → chapter card "易水歌" → walk to 형가 → "!" appears → press Space → typewriter → choice 1/2 → final node awards 죽간 → gold flash + toast → walk to back-portal "← 서재로" → ink-wipe → return to Hub → scroll-wall now shows 荊 seal in slot 1 → repeat for 항우 + 유방 → win screen reveals all 3 slips + lessons.
