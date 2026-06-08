# The NOYS — Additions Spec
_Based on remarks.pd + beat 'em up genre research_

---

## Genre Research Summary

Top references studied: **Streets of Rage 4**, **Castle Crashers**, **TMNT: Shredder's Revenge**,
**Fight 'N Rage**, **River City Girls**, **Scott Pilgrim vs. the World**, **Double Dragon Neon**.

### What makes great beat 'em ups (feasible in Pygame):

| Feature | Source game | Feasibility |
|---|---|---|
| Unique magic per character | Castle Crashers, TMNT SR | ✅ Easy |
| Ranged enemies (projectile throwers) | Streets of Rage 4, River City Girls | ✅ Easy |
| Jumping enemies (leap over attacks) | Fight 'N Rage, SoR4 | ✅ Easy |
| Self-healing enemies | SoR4 | ✅ Easy |
| Pit hazards (fall = damage/death) | TMNT SR, Double Dragon | ✅ Moderate |
| Platforms to stand on | TMNT SR, Castle Crashers | ✅ Moderate |
| Floor items / pickups (food, potions) | Castle Crashers, Scott Pilgrim | ✅ Easy |
| Collectible currency → extra life | Castle Crashers | ✅ Easy |
| Falling hazards during boss fights | Various | ✅ Moderate |
| Boss multi-phase with unique moves | SoR4, Castle Crashers | ✅ Moderate |
| Second attack button (punch + kick tradeoff) | SoR4, Fight 'N Rage | ✅ Easy |
| Dodge roll | SoR4 | ✅ Easy |
| Character-specific co-op summon | TMNT SR | ✅ Easy |
| Unlockable character | SoR4, Castle Crashers | ✅ Easy |
| Game over flavor text | Scott Pilgrim ("You are defeated!") | ✅ Trivial |
| Browser play (Pygbag/WASM) | N/A | ⚠️ Complex (own milestone) |

---

## Pre-Milestone Fixes (do before Milestone 1)

These are bugs and baseline changes, not features.

1. **Fix Boss `_die_timer` AttributeError** — `enemy.py` Boss class is missing `_die_timer`
   initialization in `__init__`. Add `self._die_timer = 0` alongside the other timer fields.

2. **Fullscreen mode** — In `game.py`, change `pygame.display.set_mode((W, H))` to
   `pygame.display.set_mode((W, H), pygame.FULLSCREEN)`. Add ESC to exit fullscreen / quit.

3. **Rename game to "The NOYS"** — Update title in `game.py` (`pygame.display.set_caption`),
   menu screen heading text, and any references to "LotemAxe" in UI strings.

---

## Milestone 1 — Polish, Controls & Collectibles

**Goal**: The game feels complete and fun even before new content. Focused on fixing what's
rough, improving feedback, and adding the collectible loop.

### 1.1 Entry Screen Image
- Replace the current menu background with `images/entry_screen.png` as the background.
- Keep title text ("The NOYS"), hi-score, and start prompt overlaid on top.

### 1.2 Two Attack Buttons + Remapped Controls
- **Insert** = Light Attack (current attack — fast, 3-hit combo, low damage)
- **Delete** = Heavy Attack (new — single slow hit, higher damage, wider hitbox, longer cooldown)
- **Home** = Magic / Special (was Delete — costs mana)
- Update `settings.py` key constants and `player.py` `handle_input()`.
- Heavy attack stats: 1.4× combo-finisher damage, 1.5× hitbox width, 2× cooldown, no combo chain.
- Gamepad: A = jump, B = light attack, X = heavy attack, Y = magic.

### 1.3 Healing Pickups
- New entity class `Pickup` in a new file `pickups.py` (or bottom of `level.py`).
- Two types placed at fixed world_x positions in each level's spawn table:
  - **Milk bottle**: Restores 25 HP. Small white bottle sprite (procedural: white rect + cap).
  - **Smoked salmon**: Restores 50 HP. Pink/orange slab (procedural: colored rect).
- Player walks over pickup rect to collect. Show `+25 HP` / `+50 HP` float text above player.
- Place ~4-6 pickups per level, spaced between hard spawn groups.

### 1.4 Crystal Collectibles
- New pickup type: **Crystal** (small cyan diamond, procedural draw).
- Scattered around levels (10-15 per level), also rare drop from Heavies (20% chance).
- Tracking: `player.crystals` counter.
- Every 100 crystals → gain 1 extra heart (max 5 hearts / lives). Reset crystal counter.
- Crystal count shown in HUD next to lives (small cyan number).

### 1.5 Brown Dog Collectible
- Rare pickup (1 per level, hidden near edge of screen): **Brown dog** icon (procedural draw).
- Worth 10 crystals + instantly fills mana to full.
- Show floating text: "Woof! +10 crystals, mana full!"

### 1.6 Game Over Flavor Text
Display one of these lines randomly below "GAME OVER":

```
English fallback:         Hebrew:
"Mom said it's bedtime."  "אמא אמרה שעת שינה"
"Go clean your room."     "לך לסדר את החדר"
"You have homework!"      "יש לך שיעורי בית"
"No dessert for you!"     "אין קינוח בשבילך"
```

- Try to render Hebrew with a Unicode-capable font (e.g., Arial / system font fallback).
- If Hebrew fails to render, fall back to English.
- Random pick each time game over triggers.

---

## Milestone 2 — Character Identity & Enemy Variety

**Goal**: Each character feels different to play. Enemies feel like distinct threats, not
just stat clones.

### 2.1 Character-Unique Magic / Special (Home button)

Replace the one-size-fits-all magic blast with per-character specials. Cost and cooldown
remain the same (30 mana, 90-frame cooldown).

| Character | Special | Description |
|---|---|---|
| **Asaf** (dad) | Power Slam | Current magic blast, upgraded: wider radius (200px), stronger knockback. |
| **Lotem** (son) | Pee Stream | Short-range arc spray (120px, 30° cone in front). Stuns enemies for 90 frames, yellow particles. Very funny. |
| **Gal** (twin 1) | Tornado Kick | Spinning kick in place, damages all enemies within 150px radius, launches them upward. Gal spins 360° visually. |
| **Nitay** (twin 2) | Twin Assist | Gal teleports in from the side, performs a flying kick through all enemies on screen (left→right or right→left), then disappears. |

- Magic special is tied to `player.char` (set at color select screen).
- Each has unique particle color set and sound (extend `sfx.py`).

### 2.2 Nitay Boxing Gloves
- When drawing Nitay procedurally (and in sprite mode), add red boxing glove rects
  on both fists during attack frames.
- Slightly increase Nitay's light attack damage (×1.15) to reflect the gloves.

### 2.3 Enemy Variety — 3 New Enemy Types

#### Thrower (Ranged Grunt)
- Inherits from Grunt. Stops at range 250px and throws axes.
- **Axe projectile**: travels horizontally, damages player on contact (10 dmg).
  Simple rect, drawn as a spinning brown shape (rotate angle per frame).
- Throw cooldown: 120 frames. Retreats if player gets within 80px.
- HP: 40, worth 150 points.

#### Jumper (Acrobatic Grunt)
- Inherits from Grunt. Every 90 frames when player is >100px away: leaps toward player
  (vy = -13, lands near player). Attack on landing (12 dmg, wide hitbox).
- Harder to hit during jump (hitbox shrinks 40%).
- HP: 45, worth 150 points.
- Procedural draw: lighter colored helmet, spring-loaded legs (extra rectangle).

#### Healer (Support Grunt)
- Stands back and pulses green. Every 180 frames heals nearest enemy for 20 HP.
  Green particles radiate outward from Healer to target.
- Won't attack player directly; runs away if player is within 100px.
- HP: 35 (fragile — priority target). Worth 200 points.
- Draw: white/green robe instead of armor.

Add these to `settings.py` SPAWNS tables (introduce from Level 2 onwards;
first appear as rare solo spawns in late Level 1).

### 2.4 Platform Hazards

#### Pits
- Define pit zones in `settings.py`: list of `(world_x_start, world_x_end)` ranges.
- In `game.py` update loop: if entity center_x falls in a pit range and entity is on ground,
  apply `vy = -2` (slight bounce) or just deal 30 damage + knockback upward.
- Alternatively: if entity's y exceeds GROUND_Y + 40, trigger fall_into_pit().
  Players lose 30 HP and respawn at pit edge. Enemies die instantly.
- Visual: draw a dark gap in the ground strip in `level.py` for those x ranges.
- Place 1-2 pits per level, near tense fight sections.

#### Elevated Platforms
- Define platform rects in `settings.py`: `(world_x, world_y, width)`.
- Collision: if entity is falling (vy > 0) and feet cross platform top → land.
- Enemies can walk onto platforms (extend AI pathfinding minimally: if target_y < self.y, jump).
- Pickups can be placed on platforms (slightly harder to reach).

---

## Milestone 3 — Bosses, Hazards & Unlockables

**Goal**: Bosses are memorable encounters. Post-game content gives replayability.

### 3.1 Boss 1 Upgrade (existing Boss, reworked)
Current boss gets 2 improved attacks:

- **Long Sword Lunge**: Wind-up 30 frames (boss pulls back), then extends hitbox 180px
  forward for 12 frames (telegraphed by yellow glow). Damage: 35.
- **Ground Slam**: Boss jumps (vy = -12), on landing creates shockwave rect
  (full width of screen, 40px tall at ground level), damages players for 20 HP.
  Triggered when at 25% HP.
- Phase 2 charge already exists — reduce its cooldown to 120 frames (harder).

### 3.2 Boss 2 — School Teacher
New Boss class `TeacherBoss(Boss)` in `enemy.py`.

- **Stats**: 500 HP, 20 dmg, 1.2 speed. Wears glasses, ruler weapon (long rect).
- **Ruler Sweep**: Wide horizontal hitbox (250px), 25 dmg. Telegraphed with "SILENCE!" text.
- **Blackboard Throw**: Throws chalk/eraser projectile (same as Thrower axe but faster, 18 dmg).
- **Falling Hazards** (see 3.3) active during this boss fight.
- **Phase 2** (≤50% HP): Calls in 2 Grunt reinforcements every 300 frames.
- Procedural draw: gray/black suit, big glasses (two circles), ruler arm.
- Placed at world_x 7700 of Level 2 (replaces current boss, or add a Level 3).

### 3.3 Falling Hazards System
- Active during TeacherBoss fight (and optionally toggle-able for other bosses).
- Every 200–300 frames (random), spawn a **falling object** at random screen_x, y = -20.
- Falls at vy = 8–12 (random). If it hits player ground rect: 15 dmg.
- Object types (random pick): school bag (brown rect), broccoli (green triangle cluster),
  piece of clothing (irregular polygon).
- Visual: object visible as it falls, small dust cloud on ground impact.
- Warn player: brief shadow/indicator on ground 60 frames before impact (like Cuphead).

### 3.4 Boss 3 — Roller Blade Boss
New class `RollerBoss(Boss)`.

- **Stats**: 350 HP, 18 dmg, very high speed (3.5 base).
- **Skate Dash**: Every 80 frames, charges at full speed (5.0) across entire screen.
  Damages any player in path (22 dmg). Bounces off world edges, does 2 passes.
- **Spin Attack**: Spins in place for 60 frames, 100px radius hitbox (12 dmg).
- Harder to hit because of speed — players must time attacks to landing pauses.
- Procedural draw: inline skates (extra rect at feet), speed lines behind.
- Place on Level 3 (or as optional secret level accessible after beating Level 2).

### 3.5 "Nice to Have" Bosses
Two optional bosses, simpler to implement if time allows:

- **Toothbrush Boss**: Giant toothbrush as weapon, can spit toothpaste (ranged, slows player),
  defeated by hitting its bristles.
- **Spiderman Boss**: Web throw (stuns player in place for 60 frames), wall climb
  (disappears to top of screen, re-enters from opposite side).

These are fun but non-critical — add only if Milestone 3 core is solid.

### 3.6 Unlock Yael
- After defeating the final boss: set `game.yael_unlocked = True`, save to same file as hi-score.
- Yael appears as a 5th option in the COLOR_SELECT screen.
- Sprite loaded from `images/Yael.png` (same pipeline as other characters in `sprites.py`).
- Unique stats: faster speed (×1.2), lower HP (75), unique special (TBD — placeholder: same as Asaf).
- On the victory/credits screen: show "Yael Unlocked!" banner.

### 3.7 Browser Deployment (Pygbag)
The game cannot deploy to Vercel as-is (Vercel = serverless JS/Python web functions,
not a game host). The correct approach:

1. **Install pygbag**: `pip install pygbag`
2. **Run**: `python -m pygbag main.py` — compiles game to WebAssembly.
3. **Output**: `build/web/` folder with an `index.html`.
4. **Host**: Deploy `build/web/` to GitHub Pages (free), Netlify, or itch.io.
5. **Code changes needed**: 
   - Replace `while True` game loop with `async def main()` + `await asyncio.sleep(0)` yield.
   - Remove or wrap `numpy` sound synthesis (numpy has partial WASM support — test carefully).
   - `highscore.txt` file I/O won't work in browser — use `localStorage` via JS bridge or disable.

This is a non-trivial refactor. Recommend doing it last, after all gameplay is solid.

---

## Implementation Order Summary

```
Pre-milestone  →  Fix Boss _die_timer + fullscreen + rename to "The NOYS"
Milestone 1    →  Entry screen, 2 attack buttons, pickups (milk/salmon/crystals/dog), game over text
Milestone 2    →  Per-character specials, Nitay gloves, 3 new enemy types, pits + platforms
Milestone 3    →  Boss 1 upgrade, Teacher boss + falling hazards, Roller boss, Yael unlock, browser
```

Each milestone is independently testable. Milestone 1 has zero dependencies on later work.
Milestone 2 requires the new attack button from M1. Milestone 3 requires nothing from M1/M2
except the general codebase shape.
