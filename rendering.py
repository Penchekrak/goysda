import pygame
from utils import colors


def render(screen, game_state):
    screen.fill(colors.get('red'))

    for placed_stone in game_state.placed_stones:
        pygame.draw.circle(screen, colors.get(placed_stone.color), (placed_stone.x, placed_stone.y), 10)