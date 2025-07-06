import pygame
from utils import colors
import random
import math
from utils import default_config

from render_tempates.background_water import render_water_background

def create_single_cloud(surface, config):
    random_cloud_coord = (random.randint(0, config['width']), random.randint(0, config['height']))
    for _ in range(int(math.floor(config['cloud_bulkiness'] / 2))):
        pygame.draw.circle(surface, colors.get('white'), (random_cloud_coord[0], random_cloud_coord[1]), config['cloud_bulk_radius'])
        pygame.draw.circle(surface, colors.get('white'), (random_cloud_coord[0] + config['width'], random_cloud_coord[1]), config['cloud_bulk_radius'])
        random_radius = random.uniform(config['cloud_bulk_radius'] / 2, config['cloud_bulk_radius'])
        random_angle = random.uniform(0, 2 * math.pi)
        random_cloud_coord = (random_cloud_coord[0] + random_radius * math.cos(random_angle), random_cloud_coord[1] + random_radius * math.sin(random_angle))
    for _ in range(int(math.ceil(config['cloud_bulkiness'] / 2))):
        pygame.draw.circle(surface, colors.get('light_grey'), (random_cloud_coord[0], random_cloud_coord[1]), config['cloud_bulk_radius'])
        pygame.draw.circle(surface, colors.get('light_grey'), (random_cloud_coord[0] + config['width'], random_cloud_coord[1]), config['cloud_bulk_radius'])
        random_radius = random.uniform(0, config['cloud_bulk_radius'])
        random_angle = random.uniform(0, 2 * math.pi)
        random_cloud_coord = (random_cloud_coord[0] + random_radius * math.cos(random_angle), random_cloud_coord[1] + random_radius * math.sin(random_angle))
    return surface

def create_clouds(config):
    surface = pygame.Surface((config['width'] * 2, config['height']))
    surface.fill(colors.get('blue'))
    for _ in range(config['cloud_count']):
        create_single_cloud(surface, config)
    return surface

cloudy_surface = create_clouds(default_config)

def render_clouds(screen, game_state, config):
    screen.blit(cloudy_surface, (game_state.background_state - config['width'], 0))

def render_background(screen, game_state, config):
    if getattr(game_state, 'background_to_render', 'clouds') == 'clouds':
        render_clouds(screen, game_state, config)
    elif getattr(game_state, 'background_to_render', 'clouds') == 'water':
        render_water_background(screen, game_state, config)
    else:
        screen.fill(colors.get('black'))

def render_board(screen, game_state, config):
    delta_x, delta_y = (config['width'] - config['board_width']) / 2, (config['height'] - config['board_height']) / 2
    board_display = pygame.Surface((config['board_width'], config['board_height']))
    board_display.blit(screen, (-delta_x, -delta_y))
    # board_display = pygame.transform.scale_by(board_display, 1.1)
    board_display = pygame.transform.box_blur(board_display, config['board_blur_radius'])
    transparent_board = pygame.Surface((config['board_width'], config['board_height']), pygame.SRCALPHA)
    transparent_board.fill(config['board_color'] + (200, ), special_flags=pygame.BLEND_RGBA_ADD)
    board_display.blit(transparent_board, (0, 0))

    # отрисовка бордерной зоны
    
    for placed_stone in game_state.get_list_of_stones_to_draw():
        pygame.draw.circle(
            board_display, 
            config['stone_no_click_zone_color'],
            (placed_stone.x - delta_x, placed_stone.y - delta_y),
            config['stone_radius'] * 2
        )
    
    # отрисовка настоящих кругов
    for placed_stone in game_state.get_list_of_stones_to_draw():
        pygame.draw.circle(
            board_display,
            colors.get(placed_stone.color),
            (placed_stone.x - delta_x, placed_stone.y - delta_y),
            config['stone_radius']
        )
    
    screen.blit(board_display, (delta_x, delta_y))

def render(screen, game_state, config):
    screen.fill(colors.get('black'))
    render_background(screen, game_state, config)
    

    render_board(screen, game_state, config)
    
    
    info = game_state.get_info()
    font = pygame.font.Font('freesansbold.ttf', 12)
    text = font.render("\n".join([f"{key}: {value}" for key, value in info.items()]), antialias=True, color="white") 
    
    
    # change_background_info_text = font.render(f"Toggle background on button: B", antialias=True, color="white") 
    screen.blit(text, (100, 400))
