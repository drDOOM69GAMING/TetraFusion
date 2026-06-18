# TetraFusion

A feature-rich Tetris game built with **Python 3** and **Pygame**.  
Created by **drDOOM69GAMING**.

## Download

Grab the latest **AppImage** from [Releases](https://github.com/drDOOM69GAMING/TetraFusion/releases) — no install required, just run it.

```bash
chmod +x TetraFusion-2.0-x86_64.AppImage
./TetraFusion-2.0-x86_64.AppImage
```

Settings and high scores are saved to `~/.tetrafusion/`.

## Features

### Game Modes
- **Marathon** — Classic endless play, level up every 10 lines.
- **Sprint** — Clear 40 lines as fast as possible.
- **Ultra** — Score as many points as you can in 3 minutes.
- **Training** — No game over. Topping out clears the board. Press `H` to delete the bottom row.
- **Master** — Starts at level 15 with 200 ms base speed.

### Mechanics
- **SRS Wall Kicks** — Full Super Rotation System (JLSTZ + I-piece kick tables).
- **Lock Delay** — 500 ms timer, resets on move/rotate (max 15 resets).
- **7-Bag Randomizer** — Fair piece distribution.
- **5-Piece Next Queue** — Plan ahead.
- **Hold Piece** — Save a piece for later (once per drop).
- **Ghost Piece** — Shows where the piece will land.
- **T-Spin Detection** — 3-corner rule awards 400 × level bonus.
- **Scoring** — Combo (Ren) counter, Back-to-Back Tetris (1.5×), All-Clear (1200 × level).

### Controls

| Action | Keyboard | Mouse |
|--------|----------|-------|
| Move Left / Right | Arrow Keys | Hover over board column |
| Soft Drop | Down Arrow | Scroll Wheel |
| Hard Drop | Space | Left-Click |
| Rotate | Up Arrow | Right-Click |
| Hold | C | Middle-Click |
| Pause | P | — |
| Fullscreen Toggle | F4 | — |

Controller support is also available with fully rebindable buttons.

### Visuals
- **Themes** — Default, Retro, Dark, Pastel, 3 colorblind palettes.
- **Backgrounds** — Auto (10+ procedural patterns), Stars, Gradient, Checker, Waves, Aurora, None.
- **Particle Effects** — Flame, Wind, Water, Ice, Flicker, Matrix, None.
- **Particle Density** — Low / Medium / High.
- **Screen Shake** — Toggle on/off.
- **Ghost Piece Opacity** — Adjustable slider.
- **DAS / ARR** — Adjustable timing presets.

### Audio
- Built-in sound effects (line clear, game over, heartbeat danger zone).
- Toggle music on/off or load a custom music folder (supports MP3, OGG, WAV, FLAC, AAC, WMA, M4A).

### Other
- **Per-mode high score leaderboard** with 3-letter initials.
- **Stats tracking** (max combo, T-spin count).
- **Full help manual** in-game (press TAB to toggle fonts).
- **Fade transitions** between all menus.
- **Line clear & game over animations.**

## Run from Source

```bash
pip install pygame mutagen
python TetraFusion_2.0.py
```

## License

MIT
