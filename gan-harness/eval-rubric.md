# Evaluation Rubric: 시기열전 (Shiji Yeoljeon)

> Total: **10.0 points**. The Evaluator scores each axis, sums them, and produces a structured critique.
> All scores are floating-point. Be strict — a 9.5+ should be rare and earned.

---

## Axis 1 — Design (max 2.5 pts)

**Question:** Is the game concept well-designed and educational for Korean children aged 7–12?

| Score | Criteria |
|-------|----------|
| 2.3–2.5 | Hanji + ink + vermilion identity is consistent and intentional. Each historical scene is visually distinct at a glance. Educational content is *woven into gameplay* (e.g., breaking pots IS the 破釜沈舟 lesson), never dumped as walls of text. Tone is warm and child-appropriate; no on-screen violence even in 형가 chapter. UI hierarchy is clear with editorial asymmetry, not centered AI-slop. |
| 1.7–2.2 | Visual identity is mostly consistent. Scenes are distinguishable. Educational content is present but sometimes told rather than shown. Tone is appropriate. |
| 1.0–1.6 | Visual identity is partial or generic. Educational content is mostly text dumps. Some scenes feel interchangeable. |
| 0.4–0.9 | Looks like a generic RPG reskin. Educational angle is superficial. |
| 0.0–0.3 | No coherent design direction; doesn't feel Korean or educational. |

**Anti-pattern deductions (subtract from this axis):**
- –0.3 if title uses rainbow gradients
- –0.2 if emoji are used as icons instead of pixel glyphs
- –0.2 if background is default black instead of parchment
- –0.3 if any violence is shown on-screen (assassination, blood, etc.)

---

## Axis 2 — Originality (max 1.5 pts)

**Question:** Does it feel unique, not a generic template?

| Score | Criteria |
|-------|----------|
| 1.4–1.5 | The 죽간 collection metaphor is thematic and visually fresh. Each mini-game ties *specifically* to its historical lesson (not interchangeable). Chapter-card ink-wash transition feels handcrafted. The 사마천 hub scroll-wall is a memorable visual hook. Avoids "8-bit Mario" defaults entirely. |
| 1.0–1.3 | At least 2 of: thematic 죽간 system, lesson-tied mini-games, handcrafted transitions, scroll-wall hub. Mostly avoids generic pixel-art tropes. |
| 0.6–0.9 | Some originality in concept but execution falls back on familiar RPG patterns. Mini-games are generic (e.g., just "press space to win"). |
| 0.2–0.5 | Looks and plays like a tutorial template with names swapped. |
| 0.0–0.1 | No identifiable creative voice. |

---

## Axis 3 — Craft (max 2.0 pts)

**Question:** Is the pixel art visual quality good? Is the code clean?

### Visual craft (1.0 pt)
- Pixel art readability: a 7-year-old can recognize 항우 vs. 유방 vs. 형가 at a glance (0.4)
- Animation polish: idle bob, 2-frame walk cycle, footstep dust, dialogue typewriter all present (0.3)
- Sprites drawn programmatically (no external images), crisp pixels (`imageSmoothingEnabled = false`) (0.3)

### Code craft (1.0 pt)
- Single self-contained HTML file under ~200KB (0.2)
- Clear section organization with comment headers (CONFIG / SPRITES / TILES / DIALOGUE / etc.) (0.3)
- No `console.error` during a normal play session (0.3)
- Edge cases handled: empty inventory message, mini-game retry, localStorage fallback, mute persists (0.2)

---

## Axis 4 — Functionality (max 4.0 pts)

**Question:** Does the game actually run and play correctly?

This is the highest-weight axis. The Evaluator should mentally (or actually) walk through the critical flow.

### Boot & render (0.5)
- Opens by double-clicking the HTML file with no server (0.2)
- Canvas renders at 60fps without flicker or frame drops (0.2)
- No JS errors in console at boot (0.1)

### Movement & world (0.7)
- Arrow keys / WASD move the player smoothly in 4 directions (0.3)
- Tile collision works — player cannot phase through walls/water (0.2)
- Scene transitions work in both directions and preserve state (0.2)

### Dialogue (0.7)
- Pressing Space/Enter near an NPC opens dialogue (0.2)
- Typewriter effect runs and is skippable (0.2)
- Branching choices work — at least one NPC has ≥2 reply paths that route correctly (0.3)

### Historical content (0.8)
- At least 3 historical NPCs from 사기 are present (항우, 유방, 형가 minimum) (0.3)
- Each has lore-accurate dialogue appropriate for ages 7–12 (0.3)
- At least one mini-game is tied to a specific historical idiom (破釜沈舟 / 約法三章 / 易水歌) (0.2)

### Progression loop (0.8)
- 죽간 counter visible in HUD and increments on encounter completion (0.3)
- Tab opens 죽간 inventory showing earned slips with their lesson text (0.2)
- Hub scene exists and updates as 죽간 are collected (0.2)
- Win condition reachable: collecting all available 죽간 triggers ending or completion message (0.1)

### Critical end-to-end flow (0.5)
**Title → Hub → enter 형가 chapter → talk to 형가 → mini-game → win → 죽간 +1 → return to hub → scroll updates**
- Full flow works without manual page reload or console intervention (0.5, all-or-nothing for the last 0.3)

---

## Scoring Output Format

The Evaluator should produce JSON like:

```json
{
  "design": 2.1,
  "originality": 1.2,
  "craft": {
    "visual": 0.8,
    "code": 0.7,
    "total": 1.5
  },
  "functionality": {
    "boot": 0.5,
    "movement": 0.6,
    "dialogue": 0.6,
    "content": 0.7,
    "progression": 0.7,
    "e2e_flow": 0.5,
    "total": 3.6
  },
  "total": 8.4,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "blocking_issues": ["..."],
  "next_sprint_priorities": ["..."]
}
```

## Hard Fail Conditions (cap total at 4.0 if any apply)

- Game does not open / renders blank canvas
- Player cannot move
- No dialogue with any historical figure works
- JavaScript throws uncaught errors that halt the game loop
- Requires a server to run (uses `fetch` for local files, ES modules without bundling, etc.)
- Uses external image files (violates the no-assets constraint)

## Excellence Bonus (additive, max +0.0 — no bonus, scores cap at 10.0)

The rubric does not award bonus points. A perfect 10.0 requires excellence across all four axes; do not inflate scores to compensate for a weak axis.
