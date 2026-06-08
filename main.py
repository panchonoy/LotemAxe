import sys
import pygame
from settings import SCREEN_W, SCREEN_H, FPS, TITLE
from game import Game


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    Game(screen, clock).run()
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
