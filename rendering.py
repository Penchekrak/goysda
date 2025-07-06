import pygame
from utils import colors

def render_clouds(screen, game_state, config):
    cloud_surface = pygame.image.load(config['cloud_image_path']).convert()
    cloud_surface = pygame.transform.scale(cloud_surface, (config['cloud_scale'] * cloud_surface.get_width(), config['cloud_scale'] * cloud_surface.get_height()))
    cloud_state = game_state.cloud_state
    for cloud in cloud_state:
        screen.blit(cloud_surface, (cloud.x, cloud.y))

def render(screen, game_state, config):
    screen.fill(colors.get('black'))
    board_display = pygame.Surface((config['board_width'], config['board_height']))
    render_clouds(screen, game_state, config)
    board_display.fill(colors.get(config['background_color']))

    delta_x, delta_y = (config['width'] - config['board_width']) / 2, (config['height'] - config['board_height']) / 2
    for placed_stone in game_state.get_list_of_stones_to_draw():
        pygame.draw.circle(board_display, colors.get(placed_stone.color), (placed_stone.x - delta_x, placed_stone.y - delta_y), 10)
    
    screen.blit(board_display, (delta_x, delta_y))