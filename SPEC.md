# LotemAxe — Game Spec & Dev Plan

## Overview
Side-scrolling beat 'em up inspired by Golden Axe.  
Players fight through enemy waves across levels and defeat a boss to win.

---

## Core Design

| Item | Decision |
|------|----------|
| Genre | Beat 'em up / hack & slash |
| Players | 1–2 local co-op |
| Input | Keyboard (P1 + P2 split) and/or gamepads |
| Player character | Knight (KayKit) |
| Enemy character | Barbarian re-skin / grunt variants |
| Art style | KayKit low-poly palette — chunky, colorful, cartoonish |
| Engine | Python + Pygame |

---

## Controls

| Action | Player 1 (keyboard) | Player 2 (keyboard) | Gamepad (both) |
|--------|---------------------|---------------------|----------------|
| Move | WASD / Arrow keys | IJKL | Left stick / D-pad |
| Jump | W / Up | I | South button (A/Cross) |
| Attack | Z | , (comma) | East button (B/Circle) |
| Magic | X | . (period) | West button (X/Square) |

---

## Game Loop

```
Main Menu → (Character color pick) → Level 1 → Boss → Victory
                                                     ↓
                                               Game Over → Retry
```

---

## Entities

### Player (Knight)
- HP: 100 | Magic: 100 (regenerates over time)
- **Attack**: sword swing, short range, fast
- **Magic**: screen-blast that damages all on-screen enemies
- **Jump attack**: jump then attack for slam

### Grunt (standard enemy)
- HP: 50 | Damage: 8 per hit
- AI: walk toward nearest player, attack when in range

### Heavy (stronger enemy, added in M2)
- HP: 100 | Damage: 15 | Slower, more knockback resistance

### Boss
- HP: 400 | Damage: 22
- Phase 1: walk + attack
- Phase 2 (below 50% HP, added in M3): charge + area attack

---

## Level Structure (v1 — one level)

| Zone | Content |
|------|---------|
| 0–1500 px | Tutorial: 2 grunt waves |
| 1500–3500 px | Mid: 4 grunt waves, mixed grunts + heavies |
| 3500–5500 px | Late: dense waves, heavier enemies |
| 5500–6000 px | Boss arena |

---

## HUD
- Each player: HP bar + Magic bar (top-left / top-right)
- Shared score (center top)
- Boss HP bar appears when boss spawns (bottom center)

---

---

# Dev Plan — 3 Milestones

---

## Milestone 1 — Core Gameplay Loop ✅ Goal: playable solo, shapes only

**What works at the end:**
- Player (P1 only) can move, jump, attack, use magic
- Camera scrolls right with the player
- 3 grunt waves + 1 boss spawn as player advances
- Enemy AI: walk toward player, attack in range
- HP system, player death → Game Over screen
- Basic score counter
- Victory screen when boss is defeated

**Art:** Colored shapes matching KayKit palette
- Knight: gray rectangle body, red cape strip, round head
- Grunts: brown rectangle body, round head
- Boss: purple/large version

**Files to build:**
- `main.py`, `settings.py`, `player.py`, `enemy.py`, `particles.py`, `level.py`, `ui.py`, `game.py`

**Debug checklist after M1:**
- [ ] Player moves and jumps smoothly
- [ ] Sword hitbox hits enemies (not thin air)
- [ ] Enemies don't overlap / phase through player
- [ ] Magic clears screen enemies
- [ ] Boss spawns at end, has its own HP bar
- [ ] Game Over and Victory screens appear correctly
- [ ] No crashes on a full run

---

## Milestone 2 — Co-op + Better Art 🎨 Goal: 2 players, game looks like KayKit

**What's added:**
- Player 2 support (keyboard split + gamepad via `pygame.joystick`)
- Each player has independent HP / magic bar
- Players can't hit each other
- 3-hit combo chain (attack timing window)
- Knockback on enemies when hit
- Screen shake on magic blast

**Art upgrade** (still pygame.draw, no external sprites yet):
- Knight proportions match KayKit: oversized round head, stubby limbs, armor plates
- Red cape animates (simple flap)
- Enemy grunt: brown fur feel, bear-helmet shape
- Boss: large purple armored shape with crown accent
- Background: sky gradient + distant mountain silhouettes + grass strip
- Hit spark particles
- Magic: blue ring shockwave effect

**New gameplay:**
- Heavy enemy variant (slower, tankier)
- Lives system (3 lives each, shared pool in co-op)
- Hi-score saved to a local file

**Debug checklist after M2:**
- [ ] P1 and P2 both independently controllable
- [ ] Gamepad recognized and works for at least one player
- [ ] Co-op: both players can die independently, game over when both out of lives
- [ ] Combo hits register (3rd hit should stun enemy briefly)
- [ ] Screen shake fires on magic, not on normal hits
- [ ] Hi-score file written and read correctly

---

## Milestone 3 — Polish + Full Game ✨ Goal: feels like a real release

**What's added:**
- Main menu with title screen (KayKit art style logo)
- Character color selection (Knight blue / Knight red for P2)
- Level 2 with different background theme (dungeon/cave palette)
- Boss phase 2 (charge attack below 50% HP)
- SFX: sword swing, hit, magic, enemy death, boss roar (generated tones via pygame.mixer or real .wav files)
- KayKit sprite sheets integrated **if** rendered from Blender (see note below)
- Death animation (enemy tumbles, fades)
- End credits / score screen

**Art note — KayKit 3D → 2D sprites:**  
The included pack is 3D (GLB/FBX). To use real KayKit art in Pygame you need to render sprite sheets:  
1. Open `Characters/gltf/Knight.glb` in Blender (free)  
2. Set orthographic camera, fixed angle  
3. Render each animation pose as a transparent PNG  
4. Pack into a sprite sheet  
If you do this before M3 starts, we integrate the real sprites. Otherwise M3 uses the polished pygame.draw art from M2.

**Debug checklist after M3:**
- [ ] Menu → character pick → game → victory/game over → back to menu (full loop)
- [ ] Level 2 loads after level 1 victory
- [ ] Boss phase 2 triggers at 50% HP
- [ ] Sound plays on hits, magic, death (no audio lag)
- [ ] No frame-rate drops below 55 FPS during heavy particle scenes
- [ ] Hi-score persists between sessions

---

## Tech Stack

| Dependency | Use |
|------------|-----|
| `pygame >= 2.0` | Rendering, input, game loop |
| `pygame.joystick` | Gamepad support (built-in) |
| `pygame.mixer` | Audio (built-in) |
| Standard library only | No other dependencies |

Install: `pip install pygame`
