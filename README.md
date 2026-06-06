# SpiritThief

SpiritThief is a top-down dungeon crawler built with Pygame where you play as a ghost that possesses enemies and uses their abilities against them.

## Gameplay

You exist as an incorporeal spirit with a time limit. Possess nearby enemies with SPACE and control them to fight through procedurally generated dungeons. Eject to detonate the host and move on to the next victim. Gain XP, level up, and choose from unlockable mutations.

### Controls

| Key | Action |
| :--- | :--- |
| WASD / Arrow Keys | Move |
| SPACE | Possess nearest enemy |
| E | Eject from host |
| Left Click | Attack (while possessing) |
| R | Restart (on Game Over) |
| ESC | Quit |

## Enemies

- **Slime** - Fast, weak ranged attacker.
- **Skeleton** - Moderate speed, fires bone shots.
- **Iron Knight** - Slow, high-HP tank with heavy damage.

## Progression and Mutations

Defeat enemies to gain XP. On level-up, choose one of three mutations:

- **Corpse Explosion** - Ejecting detonates the host in an area-of-effect blast.
- **Time Thief** - Kills restore spirit time.
- **Spirit Haste** - Spirit form moves 50% faster.

Each dungeon floor scales enemy count and difficulty. Reach the exit tile to descend deeper.

## Installation

Requires Python 3.8+ and Pygame.

```bash
pip install pygame
python main.py
```

## Project Structure

- `main.py` - All game logic, entities, AI, rendering, and event loop.
- `assets/` - Sprite images (floor, wall, enemies, spirit). Falls back to solid colors if missing.

## License

MIT
