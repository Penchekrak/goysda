import random
import math
from utils import default_config, calculate_deltax_deltay, convert_polygon_with_hole_to_polygon_without_hole

import pygame
import shapely
from utils import colors

from render_tempates.background_water import render_water_background
from render_tempates.real_board import create_real_board_surface

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
real_board_cached_surface = create_real_board_surface(default_config)

def render_clouds(screen, game_state, config):
    screen.blit(cloudy_surface, (game_state.background_state - config['width'], 0))

def render_background(screen, game_state, config):
    background_to_render = game_state.background_to_render_list[game_state.background_to_render_index]
    if background_to_render == 'clouds':
        render_clouds(screen, game_state, config)
    elif background_to_render == 'water':
        render_water_background(screen, game_state, config)
    else:
        screen.fill(colors.get('black'))

def render_limpid_board(screen, game_state, config, delta_x, delta_y):
    board_display = pygame.Surface((config['board_width'], config['board_height']))
    board_display.blit(screen, (-delta_x, -delta_y))
    # board_display = pygame.transform.scale_by(board_display, 1.1)
    board_display = pygame.transform.box_blur(board_display, config['board_blur_radius'])
    # transparent_board = pygame.Surface((config['board_width'], config['board_height']), pygame.SRCALPHA)
    transparent_board = pygame.Surface((config['board_width'], config['board_height']))
    transparent_board.fill(config['board_color'] + (200, ), special_flags=pygame.BLEND_RGBA_ADD)
    board_display.blit(transparent_board, (0, 0))

    return board_display

def render_cached_real_board(screen, config, delta_x, delta_y):
    board_display = pygame.Surface((config['board_width'], config['board_height']), pygame.SRCALPHA)
    board_display.blit(real_board_cached_surface, (0, 0))
    return board_display

def render_board(screen, game_state, config, transformation):
    import copy
    delta_x, delta_y = calculate_deltax_deltay(config)
    board_to_render = game_state.board_to_render_list[game_state.board_to_render_index]

    base_surface = pygame.Surface((config['board_width'], config['board_height']), pygame.SRCALPHA)
    base_surface.fill((0, 0, 0, 0))
    # if board_to_render == 'real':
    #     board_display = render_cached_real_board(screen, config, delta_x, delta_y)
    # elif board_to_render == 'limpid':
    #     board_display = render_limpid_board(screen, game_state, config, 0, 0)
    # else:
    #     raise ValueError(f"Unknown board to render: {game_state.board_to_render_list[game_state.board_to_render_index]}")
    
    # corner_1_and_3 = []
    # for x, y in [[delta_x, delta_y], [config['board_width'] + delta_x, config['board_height'] + delta_y]]:
    #     corner_1_and_3_elem = transformation.world_to_screen(x, y)
    #     corner_1_and_3_elem = [corner_1_and_3_elem[0] - delta_x, corner_1_and_3_elem[1] - delta_y]
    #     corner_1_and_3.append(corner_1_and_3_elem)
    # corner1, corner3 = corner_1_and_3

    # base_surface.blit(pygame.transform.scale(board_display, (corner3[0] - corner1[0], corner3[1] - corner1[1])), corner1)
    polygons_list = []
    for polygon_or_multipolygon, color in game_state.get_list_of_shapes_to_draw():
        if type(polygon_or_multipolygon) == shapely.Polygon:
            polygons_list.append((polygon_or_multipolygon, color))
        elif type(polygon_or_multipolygon) == shapely.MultiPolygon:
            polygons_list.extend([(polygon, color) for polygon in polygon_or_multipolygon.geoms])
        else:
            raise NotImplementedError
    
    polygons_list2 = []
    for polygon, color in polygons_list:
        if "_hollow" in color:
            color = color.replace("_hollow", "")
            polygon_exterior_thicked = shapely.intersection(polygon.exterior.buffer(config["line_width"]), polygon)
            polygons_list2.append((convert_polygon_with_hole_to_polygon_without_hole(polygon_exterior_thicked), color))
        else:
            polygons_list2.append((polygon, color))
    polygons_list = polygons_list2

    for polygon, color in polygons_list:
        if len(polygon.exterior.coords) > 2:
            tranformed_coords = [transformation.world_to_screen(elem[0], elem[1]) for elem in polygon.exterior.coords] # 
            pygame.draw.polygon(base_surface, colors[color], [[tcoord_x - delta_x, tcoord_y - delta_y] for tcoord_x, tcoord_y in tranformed_coords])

    screen.blit(base_surface, (delta_x, delta_y))

def draw_info_panel(screen, game_state, config):
    font_key = pygame.font.SysFont('Courier New', 14)
    font_value = pygame.font.SysFont('Courier New', 14)
    
    info = game_state.get_info()
    
    panel_width = 800
    line_height = 20
    padding = 10
    
    panel_height = (len(info) * line_height) + (2 * padding)
    panel_x = (config['width'] - panel_width) / 2
    panel_y = config['height'] - panel_height - 10
    
    panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel_surface.fill((0, 0, 0, 150))
    
    key_color = (200, 200, 200) # Light grey for keys
    value_color = (255, 255, 255) # White for values
    
    key_x = padding
    value_x = panel_width * 0.6  # Start values at 60% of the panel width

    pixel_eps = 4
    
    for i, (key, value) in enumerate(info.items()):
        # Render Key
        key_surface = font_key.render(f"{key}:", True, key_color)
        panel_surface.blit(key_surface, (key_x, padding + i * line_height))
        
        # Render Value
        value_surface = font_value.render(str(value), True, value_color)
        panel_surface.blit(value_surface, (value_x, padding + i * line_height))
        
        # Draw separator line
        if i < len(info) - 1:
            line_y = (padding + pixel_eps) + (i + 1) * line_height - (line_height / 2) + 2
            line_color = (100, 100, 100, 150) # Semi-transparent grey
            pygame.draw.line(panel_surface, line_color, (padding, line_y), (panel_width - padding, line_y), 1)


    screen.blit(panel_surface, (panel_x, panel_y))


def render(screen, game_state, config, transformation):
    screen.fill(colors.get('black'))
    render_background(screen, game_state, config)
    render_board(screen, game_state, config, transformation)
    draw_info_panel(screen, game_state, config)
    