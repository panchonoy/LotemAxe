"""
Pre-process all character sprite frames and save as individual RGBA PNGs
into images/processed/<char>_<anim>_<idx>.png

Run this script once locally before building/deploying:
    python process_sprites.py

Pygbag/WASM cannot run PIL at runtime, so baking sprites to PNG files
lets the browser build load them with plain pygame.image.load().
"""
import os, sys
import pygame

def main():
    os.makedirs('images/processed', exist_ok=True)

    # Must import sprites AFTER pygame is partially initialized
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((1, 1))

    import sprites as sp
    sp.init()

    if not sp.is_ready():
        print('ERROR: sprite init failed — check PIL/numpy are installed.')
        sys.exit(1)

    count = 0
    for char, frames_dict in sp._CHAR_FRAMES.items():
        for anim, rects in frames_dict.items():
            for idx in range(len(rects)):
                surf = sp._cache.get((char, anim, idx))
                if surf is None:
                    print(f'  MISSING: {char}/{anim}/{idx}')
                    continue
                out_path = f'images/processed/{char}_{anim}_{idx}.png'
                pygame.image.save(surf, out_path)
                count += 1

    print(f'Saved {count} sprite frames to images/processed/')
    pygame.quit()

if __name__ == '__main__':
    main()
