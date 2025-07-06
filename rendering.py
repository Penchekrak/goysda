import pygame
from utils import colors


def render(screen, game_state, config):
    screen.fill(colors.get(config['background_color']))

    for placed_stone in game_state.placed_stones:
        pygame.draw.circle(screen, colors.get(placed_stone.color), (placed_stone.x, placed_stone.y), 10)