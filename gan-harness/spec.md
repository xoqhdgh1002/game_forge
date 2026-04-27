# Product Specification: 시기열전 (Shiji Yeoljeon) — 사마천의 발자취

> Generated from brief: "사마천의 사기(史記) 기반 2D 픽셀 RPG — 아이들이 역사 인물(항우, 유방, 형가 등)을 만나며 중국 역사를 배우는 탐험 게임"

## Vision

**시기열전 (Shiji Yeoljeon)** is a top-down 2D pixel-art exploration RPG where Korean children aged 7–12 step into the sandals of a young scribe-apprentice of 사마천(司馬遷). The player wanders three handcrafted "memory provinces" of ancient China, encounters legendary figures from the 史記 (項羽, 劉邦, 荊軻, 始皇帝, 韓信), unlocks their stories through dialogue mini-quests, and collects 죽간(bamboo slips) that record what they have learned. The feel is a cozy Stardew-meets-storybook tone — warm, curious, never violent — with hanji-paper UI overlays and brushed-ink chapter cards that make history feel like a living scroll.

## Design Direction

- **Color palette**:
  - Parchment background `#F4E8C8` (hanji cream)
  - Ink primary `#1F1A14` (sumi black-brown)
  - Vermilion accent `#C8392E` (도장 red)
  - Jade highlight `#3F8E6B` (역사 quest marker green)
  - Imperial gold `#D4A437` (XP / 죽간 reward)
  - Twilight sky `#3B4F7A` (night / 형가 scene)
  - Plum royal `#7A2E4D` (boss / emperor)
- **Typography**:
  - Title & headers: a brush-style Korean web font (`Nanum Brush Script`, fallback `serif`)
  - Body / dialogue: `Nanum Gothic` 14–16px, tight line-height for kids
  - Damage / XP popups: monospace pixel feel via `Galmuri11` if available, else `monospace`
  - Hierarchy: 28pt 챕터 제목 → 18pt NPC 이름 → 14pt 본문
- **Layout philosophy**: A 16:9 canvas (960×540 logical, scaled to fit). Game world fills the canvas; UI rides on translucent hanji-paper bands top (HUD: 이름, 죽간 카운트, 챕터) and bottom (대화창, 선택지). No floating cards, no rounded modern toasts — everything looks stamped, sealed, or brushed.
- **Visual identity**:
  - Every pixel is drawn with `ctx.fillRect` at 2–3px "pixel size" — no external images
  - Tilemap uses 16×16 logical tiles upscaled 2× → 32px on screen
  - Subtle 1-frame "breathing" idle on NPCs (vertical 1px bob every 500ms)
  - Walking has 2-frame leg swap, not 4 — keeps it readable and cute
  - Dialogue boxes have a vermilion 도장(stamp) seal in the corner with the character's surname (項, 劉, 荊…)
  - Scene transitions: ink-wash wipe (a `<canvas>` brush stroke that sweeps left→right)
  - Footstep dust: 2-pixel puff that fades over 200ms
- **Inspiration**: Stardew Valley's tile readability, Pokémon G/S NPC density, the 한국사 교과서 삽화 of 채상우, the brushed chapter cards of *Sekiro*, and the warm storybook tone of *Tunic*.
- **Anti-AI-slop directives**:
  - Do NOT use rainbow gradients on the title screen
  - Do NOT use generic "8-bit Mario" green pipes or red mushrooms
  - Do NOT center every UI element — use editorial asymmetry (HUD anchors top-left, 죽간 counter top-right with seal)
  - Do NOT use emoji as icons; draw small pixel glyphs (붓, 죽간, 검, 술잔)
  - Do NOT default to a black background — parchment is the canvas
  - Avoid generic "QUEST!" exclamation popups; use a pixel ink-drop animation instead

## Historical Content (사기 chapters represented)

The game adapts five 사기 episodes, simplified for ages 7–12. Each is age-appropriate (no on-screen violence; assassinations are described in narration, never shown).

1. **荊軻 (형가) — 자객열전** "역수의 노래"
   - Setting: 易水 riverbank at dusk, twilight palette
   - Lesson: courage vs. recklessness; "風蕭蕭兮易水寒" introduced as a 4-line poem the child can read aloud
2. **項羽 (항우) — 항우본기** "거록의 솥을 깨다(破釜沈舟)"
   - Setting: river crossing camp, vermilion banners
   - Lesson: the idiom 破釜沈舟 — committing fully; mini-game: choose to break the cooking pots or keep them
3. **劉邦 (유방) — 고조본기** "약법삼장(約法三章)"
   - Setting: 함양(咸陽) gate, jade and gold palette
   - Lesson: simple fair laws beat cruel complex ones; child picks 3 laws from a list of 6
4. **始皇帝 (시황제) — 진시황본기** "만리장성과 분서갱유"
   - Setting: Great Wall construction site at dawn
   - Lesson: ambition vs. cost; balanced presentation, not demonized
5. **韓信 (한신) — 회음후열전** "과하지욕(胯下之辱)"
   - Setting: 회음 marketplace
   - Lesson: enduring small humiliation for a larger goal; 인내(patience) idiom

Plus a framing character: young **司馬遷** (the player's mentor) who appears at chapter start/end and writes the collected 죽간 into the great scroll.

## Features (prioritized)

### Must-Have (Sprint 1–2)

1. **Tile-based overworld with 4-direction movement**
   - Arrow keys / WASD; player sprite is 16×16 with 2-frame walk cycle per direction
   - Collision with walls, water, furniture
   - Acceptance: player can walk smoothly at 60fps across a 30×20 tile map without phasing through obstacles
2. **NPC dialogue system with branching choices**
   - Press `Space` / `Enter` to talk; typewriter text effect at ~30 chars/sec, skippable with second press
   - Up to 3 reply choices per node; choices can set quest flags
   - Acceptance: a single NPC conversation tree of ≥6 nodes works end-to-end with at least one branch
3. **Three explorable scenes (易水 / 거록 / 함양)**
   - Each with distinct palette, tile set, ambient props (river, banners, gates)
   - Scene transitions via map edges or doorways with ink-wash wipe
   - Acceptance: player can walk between all three scenes and state persists
4. **죽간 (bamboo slip) collection system**
   - Each completed historical encounter awards 1 죽간 with the chapter title and a 1-sentence lesson
   - Top-right HUD shows `🎋 3 / 5` (drawn as pixel slips, not emoji)
   - Acceptance: opening the 죽간 inventory (`Tab` key) shows a scroll listing earned slips with their text

### Should-Have (Sprint 3–4)

5. **Three mini-game encounters (one per must-have scene)**
   - 형가: rhythm-tap to recite the 易水歌 (4 beats, hit `Space` on glow)
   - 항우: choose-your-pot mini-game (click 3 of 6 cooking pots to "break")
   - 유방: pick 3 laws from 6 cards; correct trio (살인/상해/도둑) unlocks scene
   - Acceptance: each mini-game has a clear win condition, retry option, and rewards a 죽간
6. **Chapter-start cinematic cards**
   - Full-canvas brushed ink card with vertical 한문 title + Korean subtitle, 2-second hold, dismiss on key
   - Acceptance: each scene entry shows its card exactly once per session
7. **사마천 hub scene (서재)**
   - Player returns here between chapters; 사마천 reads the latest 죽간 aloud and unlocks the next chapter portal
   - Hub has a 큰 두루마리 wall that visually fills in as 죽간 are collected
   - Acceptance: hub updates dynamically; locked portals show a 봉인 stamp until prereq is met

### Nice-to-Have (Sprint 5+)

8. **Two more scenes: 만리장성 + 회음 시장 (시황제, 한신)**
   - Brings total to 5 chapters / 5 죽간
9. **Idiom (사자성어) glossary**
   - Press `G` to open; lists 破釜沈舟, 約法三章, 胯下之辱, 焚書坑儒, 風蕭水寒 with kid-friendly meanings
   - Glossary entries unlock as their chapters complete
10. **Ambient audio (Web Audio API, no files)**
    - Procedural pentatonic 가야금-style plucks on scene entry and dialogue advance
    - Footstep tick on each tile crossed
    - Mute toggle (`M` key) with persistent localStorage flag
11. **Save / Load via localStorage**
    - Auto-save on chapter completion; "이어하기" on title screen
12. **Title screen + ending scroll**
    - Title: brushed `史記` characters with falling ink particles, "시작 / 이어하기 / 사자성어 도감" menu
    - Ending: when all 5 죽간 collected, scroll unrolls reading "사마천이 너의 이름을 사기에 적었다." with player-entered name
13. **Accessibility extras**
    - Reduced-motion toggle (disables ink-wipe and particles)
    - Text speed slider (느림/보통/빠름)
    - Large-text mode for younger readers

## Win / Lose / Progress Conditions

- **Win**: collect all 5 죽간 → ending scroll cinematic → name engraved
- **Lose**: there is no fail state. Mini-games can be retried infinitely. This is intentional — children should never feel punished for not knowing history.
- **Progress markers**:
  - 죽간 counter (top-right)
  - Hub scroll fills in visually
  - Idiom glossary entries unlock

## UI Elements

- **HUD (always visible)**:
  - Top-left: 챕터 이름 on a small hanji band
  - Top-right: 죽간 counter `🎋 n / 5` with vermilion seal
- **Dialogue box (bottom, appears on talk)**:
  - Hanji background, ink border, NPC name in vermilion, body text typewritten, 도장 seal in bottom-right corner
  - Choice prompts shown as numbered ink-brushed buttons (1, 2, 3)
- **Inventory overlay (Tab)**:
  - Scroll-shaped panel listing earned 죽간 with chapter title + 1-line lesson
- **Glossary overlay (G)**:
  - Vertical list of unlocked 사자성어, each with hanja + 한글 meaning + originating chapter
- **Pause menu (Esc)**: 계속 / 저장 / 도감 / 음소거 / 처음으로
- **Title screen**: brushed `史記` logo, three menu items, falling ink particle background
- **Chapter card**: full-screen ink brushstroke reveal with vertical hanja title

## Controls

| Key | Action |
|-----|--------|
| Arrow keys / WASD | Move |
| Space / Enter | Talk / Advance dialogue / Confirm |
| 1, 2, 3 | Dialogue choices |
| Tab | 죽간 inventory |
| G | 사자성어 도감 |
| M | Mute toggle |
| Esc | Pause menu |

## Empty / Error / Loading States

- **First load**: brief "먹을 갈고 있어요…" splash (1s) while canvas initializes — drawn as a moving brush stroke, not a spinner
- **Empty inventory**: scroll shows "아직 모은 죽간이 없어요. 사람들과 이야기해 보세요!"
- **Mini-game retry**: gentle "다시 해볼까?" prompt with a single button, no scary red text
- **localStorage unavailable**: silent fallback to in-memory state; show a small "이 브라우저는 저장이 안 돼요" hanji note in pause menu

## Technical Stack

- **Single self-contained `game.html` file** — no server, no build step, no npm
- **Rendering**: HTML5 Canvas 2D, fixed logical resolution 960×540, scaled with `ctx.imageSmoothingEnabled = false` for crisp pixels
- **Language**: vanilla ES2020 JavaScript in one `<script>` tag (or a few, organized by section comments)
- **Audio**: Web Audio API only (oscillators + envelopes), no audio files
- **Storage**: `localStorage` for save state and mute flag
- **Fonts**: Google Fonts via `<link>` (Nanum Brush Script, Nanum Gothic), graceful serif/sans fallbacks
- **No external images** — all sprites and tiles drawn programmatically as colored rectangles in a sprite-data table (e.g., `'..XX..\n.XXXX.\nXX..XX'` strings parsed at startup into pixel arrays)
- **Code organization (within one file)**:
  ```
  // ===== CONFIG / PALETTE =====
  // ===== SPRITE DATA =====
  // ===== TILE MAPS =====
  // ===== DIALOGUE TREES =====
  // ===== INPUT =====
  // ===== GAME STATE =====
  // ===== RENDER =====
  // ===== UPDATE LOOP =====
  // ===== UI OVERLAYS =====
  // ===== AUDIO =====
  // ===== SAVE / LOAD =====
  // ===== BOOT =====
  ```
- **Performance budget**: must hold 60fps on a 2019 mid-range laptop; total HTML file under 200KB

## Evaluation Criteria

### Design Quality (weight: 0.25)
- Does the game feel like a *Korean children's history book come to life*, not a generic JRPG reskin?
- Is the hanji + ink + vermilion identity consistent across HUD, dialogue, and chapter cards?
- Is each historical scene visually distinguishable at a glance (palette, props)?
- Are educational moments woven into gameplay, not dumped as walls of text?

### Originality (weight: 0.15)
- Does the 죽간 collection metaphor feel fresh and thematic (vs. generic "coins")?
- Are the mini-games tied to the *specific* historical lesson (e.g., breaking pots = 破釜沈舟)?
- Does the chapter-card ink-wash transition feel handcrafted?
- Does it avoid the default "8-bit Mario" pixel-art aesthetic?

### Craft (weight: 0.20)
- Pixel art readability: can a 7-year-old recognize 항우 vs. 유방 at a glance?
- Animation polish: idle bob, walk cycle, footstep dust, dialogue typewriter
- Code organization: clear sections, no dead code, no console errors
- Edge cases handled: empty inventory message, mini-game retry, mute persists

### Functionality (weight: 0.40)
- Game opens by double-clicking the HTML file — no server needed
- Player can move, talk to at least 3 historical NPCs, and trigger their mini-games
- Dialogue system advances correctly; choices route to correct branches
- Each completed encounter awards a 죽간; counter updates; inventory shows it
- Scene transitions work both ways without state loss
- Save / load round-trip works (if implemented)
- No JavaScript errors in console during a 5-minute play session
- Critical user flow: **Title → Hub → 형가 scene → talk to 형가 → mini-game → win → 죽간 +1 → return to hub → scroll updates**

## Sprint Plan

### Sprint 1: "Walk the world" (foundations)
- Goals: get a player walking on a tilemap with collision and a working dialogue box
- Features: #1 (movement), #2 (dialogue), one test NPC, parchment palette baseline
- Definition of done: player walks across 易水 scene, talks to a placeholder 형가, dialogue typewriter advances correctly

### Sprint 2: "Three provinces" (content scaffolding)
- Goals: build all three must-have scenes with proper tilesets and transitions
- Features: #3 (three scenes), #4 (죽간 system + HUD + Tab inventory)
- Definition of done: player can walk between 易水, 거록, 함양; each has its own palette and at least one NPC; 죽간 counter increments on talk-completion

### Sprint 3: "Make it a game" (mini-games + chapters)
- Goals: each scene has its signature mini-game and proper chapter card
- Features: #5 (three mini-games), #6 (chapter cards), #7 (사마천 hub)
- Definition of done: full loop works — Hub → enter chapter → card → explore → mini-game → win → 죽간 → return to hub → wall fills in

### Sprint 4: "Make it a story" (polish + glossary)
- Goals: the experience feels educational and complete with three chapters
- Features: #9 (사자성어 glossary), audio (#10 partial), title screen (#12 partial)
- Definition of done: title screen → 3-chapter playthrough → glossary populated → ending message; no console errors

### Sprint 5: "Full sage" (extension)
- Goals: ship all 5 chapters and accessibility
- Features: #8 (장성 + 회음 scenes), #11 (save/load), #12 (full ending), #13 (a11y)
- Definition of done: complete 5-죽간 playthrough achievable in 10–15 minutes; save/resume works; reduced-motion respected
