import asyncio
import sys
import pygame
from settings import SCREEN_W, SCREEN_H, FPS, TITLE
from game import Game, PLAYING


async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    game = Game(screen, clock)

    while True:
        clock.tick(FPS)
        game._handle_events()
        if game.state == PLAYING:
            game._update()
        game._draw()
        await asyncio.sleep(0)   # yield to browser event loop (Pygbag)


if __name__ == '__main__':
    asyncio.run(main())
