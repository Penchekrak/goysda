import pygame
from utils import colors

def render_clouds(screen, game_state, config):
    cloud_surface = pygame.image.load(config['cloud_image_path']).convert()
    cloud_surface = pygame.transform.scale(cloud_surface, (config['cloud_scale'] * cloud_surface.get_width(), config['cloud_scale'] * cloud_surface.get_height()))
    cloud_state = game_state.cloud_state
    for cloud in cloud_state:
        screen.blit(cloud_surface, (cloud.x, cloud.y))

def render(screen, game_state, config):
    board_display = pygame.Surface((config['board_width'], config['board_height']))
    render_clouds(screen, game_state, config)
    board_display.fill(colors.get(config['background_color']))

    for placed_stone in game_state.placed_stones:
        pygame.draw.circle(board_display, colors.get(placed_stone.color), (placed_stone.x, placed_stone.y), 10)
    
    screen.blit(board_display, ((config['width'] - config['board_width']) / 2, (config['height'] - config['board_height']) / 2))