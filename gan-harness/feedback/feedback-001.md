# Evaluation — Iteration 1

## Scores
| Category | Max | Score | Notes |
|----------|-----|-------|-------|
| Design | 2.5 | 2.0 | Hanji+ink+vermilion identity is consistent. Editorial asymmetric HUD. No black bg, no rainbow, no emoji. Slight deduction: chapter scenes still feel sparse/template-ish; the 易水 twilight gradient is closer to "ambient overlay" than a brushed scene; educational content is mostly delivered through dialogue-walls rather than woven into spatial play. |
| Originality | 1.5 | 1.0 | 죽간 metaphor IS implemented and visually present (HUD slips, scroll-wall slots, inventory bamboo). Hanja-stamp seal is a memorable touch. BUT: the "lesson-tied mini-game" is just a multiple-choice branch in the dialog, not a discrete mini-game (generator self-admits this in `generator-state.md`). Chapter card transition is functional but not handcrafted-looking. Loses the "lesson-tied mini-game" pillar. |
| Craft | 2.0 | 1.55 | Visual: 0.75/1.0 — sprites readable, palette-distinct, walk frames present, idle bob present, dust particles present. Player and 형가 silhouettes are very similar (both blue-ink robes); 7-yo could confuse them. Code: 0.8/1.0 — clean section headers, single ~80KB file, try/catch around loop, localStorage wrapped, but ~2400 lines is a lot in one file (acceptable for spec). |
| Functionality | 4.0 | 3.55 | Boot/render solid. Movement + collision + scene transitions work. Dialog branching, typewriter, and award flow are wired correctly end-to-end. 죽간 counter and inventory work. Win condition reachable. Minor functional bugs (see below) but no blockers. |
| **TOTAL** | **10.0** | **8.10** | |

## Pass/Fail
**Result:** PASS (threshold: 7.0)

## Hard-Fail Conditions
- [x] Blank canvas on load — NO. Boot splash → title renders fine.
- [x] No movement possible — NO. Arrow keys/WASD wired through `KEY_MAP` → `keys` → `update()` → per-axis `collidesWithWorld`. 4-direction with diagonal normalization confirmed.
- [x] Requires a server — NO. No `fetch`, no ES modules. Only external dep is Google Fonts CSS link (graceful fallback to serif/sans).
- [x] Broken JS syntax — NO. Single `<script>` block, "use strict", parses cleanly. No top-level `await`. All braces balanced.
- [x] Uses external image files — NO. All sprites authored as ASCII palette strings + `ctx.fillRect`. Title `史 記` characters use `Noto Serif KR` font (graceful fallback if blocked).

No hard fails. Total is NOT capped at 4.0.

## Anti-Pattern Deductions Applied
- None applied. Title is parchment+ink+vermilion (no rainbow gradient). HUD uses pixel-drawn bamboo slips not emoji. Background is parchment. No on-screen violence (assassination only narrated by 형가 in dialog text).

## Critical Issues (must fix)
None — game is playable end-to-end.

## High Issues (should fix)
1. **Title menu navigation is broken (subtle)**: Lines 1033-1034 — both `up` and `down` do `(game.titleIdx + 1) % 2`. Up should decrement. With only 2 items it cycles correctly by accident but is wrong. Fix: `if (consume("up")) game.titleIdx = (game.titleIdx + items.length - 1) % items.length;`

2. **"시작하기" and "처음부터 다시" do the same thing** (lines 1038-1046): both branches call `loadInto("hub")` with no progress reset. The "처음부터 다시" branch should explicitly `game.collected.clear(); cardsShown.clear();` before loading. Currently misleading menu copy.

3. **Mini-games are not actual mini-games** — they are inlined choice nodes in the dialogue tree. Spec calls for "rhythm-tap to recite the 易水歌", "choose-your-pot click 3 of 6 cooking pots", "pick 3 laws from 6 cards". The current implementation answers the rubric's *content* requirement (lesson-tied) but fails the *mechanic* requirement. Fix priority for next iteration: build at least one true mini-game screen (recommend the 항우 pot-breaking — there are already pot tiles on the map at rows 7,8,10).

4. **Player sprite vs 형가 sprite are visually too similar** for the rubric's "7-yo can recognize at a glance" bar. Both are slim-shouldered, ink-robed, with similar head shapes. Player robe is `inkSoft (#4A3D2C)`, 형가 robe is `twilight (#3B4F7A)` — close in luminance. Fix: give player a more distinct silhouette (taller hat, brush in hand visible, lighter-colored sash) OR shift 형가 to a markedly different palette (deeper indigo + gold trim).

5. **Hub scroll-wall feels static**: it's a single horizontal band of 3 slips that flip from "미수집" to filled. The spec asks for "큰 두루마리 wall that visually fills in" — currently looks like a small placard, not a wall scroll. Increase visual prominence (full top band, animated unfurl per slot).

## Medium Issues (nice to fix)
1. **Tab key in browsers**: `e.preventDefault()` is correct, but if focus is on the help div or browser chrome, Tab may be lost. Consider `tabindex="0"` on canvas and call `canvas.focus()` on click (already done — good) — but on keyboard-first start, focus is on body. Should work in practice.

2. **Walk-cycle is only 2 frames per direction, BUT the leg sprite difference is very subtle** (1 pixel shift). Footstep dust at 180ms cadence helps, but the visual feedback for moving is weak. Increase contrast between `_A` and `_B` foot positions by 2-3 pixels.

3. **Glossary (G key) shows the same lesson text as the inventory** — feels redundant. Spec wanted hanja + 한글 meaning + originating chapter as a *separate* dictionary entry per 사자성어. Currently glossary just mirrors `JUKGAN_DEFS.lesson`.

4. **No pause menu** — Esc only closes overlays. Spec lists "계속/저장/도감/음소거/처음으로" pause menu; deferred per generator notes but should land in v2.

5. **No save/load** — Only mute persists. Refresh wipes 죽간. Fine for a 5-minute playthrough but fails spec sprint 5.

6. **Audio always synthesizes even when muted check is fine**, but `audioCtx` is created on first keydown — Title screen menu navigation triggers `sfxOpen()` *before* `ensureAudio()` is called by the title's action consume. Trace: keydown listener → `ensureAudio` (once)... actually it IS attached as a global once-listener, runs on first keydown. OK, no bug — just timing tight.

7. **Toast text is centered top, but the 죽간 award flash is gold full-screen overlay** — the gold flash with parchment background can feel washed-out. Consider a small ink-drop animation at the slot location instead.

8. **`renderHUD()` measures text twice** (lines 1759, 1761) — minor `ctx.font` ordering smell; the first `measureText` uses the previous font. Cosmetic.

## What Worked Well (Not Inflating, Just Calibrating)
- Per-axis collision with wall-sliding is implemented correctly (lines 1170-1178). Player won't catch on corners.
- Try/catch around the entire game loop with a Korean error message instead of crash — good defensive engineering for a kids' game.
- Footstep SFX + dust on each leg-swap (not every frame) — properly throttled.
- Dialog typewriter is skippable (line 932), choices are 1/2/3 keyed, branching for 항우 has retry-on-wrong-answer ("다시 골라보겠느냐?") which is gentle and age-appropriate.
- 항우's `g3` choice quiz IS the spec's "lesson-tied interaction" in spirit — just delivered as choice text, not a mini-game screen.
- Custom `drawExclaim` pixel speech bubble (not emoji) when player approaches NPC — matches spec anti-pattern guidance.
- Chapter cards use vertical hanja layout — feels Korean-textbook authentic.

## Actionable Feedback for Generator (next iteration priorities)
1. **Build at least one standalone mini-game screen** (highest leverage on Originality + Functionality). Recommend 항우's pot-breaking: a 6-grid of pots, click 3 to break, gold flash on each break, win on 3rd. The pot tiles already exist on the map (`o` glyph at rows 7,8,10) — wire a click handler that enters a `STATE.MINIGAME` overlay.

2. **Fix the title menu**:
   - `up` should decrement, not increment.
   - "처음부터 다시" should explicitly clear `game.collected` and `cardsShown` before loading hub.

3. **Differentiate player and 형가 sprites**:
   - Give player a visible brush in hand (one extra column of `B` palette pixel on the right side).
   - Shift 형가 robe to deeper indigo (`#1E2B4F`) with explicit gold sash.

4. **Make the scroll-wall feel like a wall**:
   - Take the full top band of the hub (rows 1-4 already reserved).
   - Per-slot unrolling animation when a 죽간 is collected (height grows over 600ms).

5. **Add a 4th NPC: 사마천 ending dialog when all 3 죽간 collected** — when player returns to hub with all 3, 사마천 should have a new dialogue ("이제 마지막 두루마리를…"), then trigger the win screen via `action: "end_game"`. Currently win triggers automatically 900ms after the 3rd award, which is abrupt.

6. **Glossary should have its own content** — add `meaning` field to `JUKGAN_DEFS` (the 사자성어 literal meaning, separate from the story lesson) and render that in `renderGlossary()`.

7. **Optional polish**: Add a tiny "footprint trail" that fades behind the player (3-4 dust particles spaced over the last second of movement) — would lift the "Stardew tile readability" vibe.

## Screenshots
N/A — code-only evaluation. Verified by reading 2407 lines of `game.html` end-to-end and tracing the state machine TITLE → loadInto(hub) → PLAYING → portal trigger → TRANSITION → loadInto(yisu) → CHAPTER_CARD → PLAYING → near-NPC consume(action) → startDialog → typewriter → choice (1/2) → moveToNode → action="award:hyeongga" → awardJukgan → 死간+1 → repeat for 항우/유방 → after 3rd award setTimeout 900ms → STATE.WIN → renderWin scrolls in.

The end-to-end critical flow specified in the rubric — **Title → Hub → enter 형가 → talk → mini-game → win → 죽간+1 → return to hub → scroll updates** — works mechanically (with the caveat that "mini-game" is a dialog choice, not a separate screen).
