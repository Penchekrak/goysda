import pygame
import random
from utils import colors

def render_real_board(screen, game_state, config, delta_x, delta_y):
    """Рендерит правдоподобную деревянную доску Go"""
    board_width = config['board_width']
    board_height = config['board_height']
    
    # Создаем поверхность для доски
    board_surface = pygame.Surface((board_width, board_height))
    
    # Создаем деревянную текстуру (статичную)
    wood_color = (139, 69, 19)  # Коричневый цвет дерева
    board_surface.fill(wood_color)
    
    # Добавляем градиент для объема (статичный)
    center_x, center_y = board_width // 2, board_height // 2
    for y in range(board_height):
        for x in range(board_width):
            pixel = board_surface.get_at((x, y))
            distance_from_center = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            factor = 1 - (distance_from_center / (board_width + board_height) * 0.1)
            new_color = tuple(max(0, min(255, int(c * factor))) for c in pixel)
            board_surface.set_at((x, y), new_color)
    
    # Добавляем рамку
    border_color = (101, 67, 33)  # Темно-коричневый
    border_width = 8
    pygame.draw.rect(board_surface, border_color, (0, 0, board_width, board_height), border_width)
    
    # Рисуем разметку доски Go
    line_color = (50, 25, 0)  # Темно-коричневый для линий
    cell_size = min(board_width, board_height) // 20
    
    # Начальная позиция сетки
    start_x = (board_width - cell_size * 18) // 2
    start_y = (board_height - cell_size * 18) // 2
    
    # Вертикальные линии
    for i in range(19):
        x = start_x + i * cell_size
        pygame.draw.line(board_surface, line_color, (x, start_y), (x, start_y + 18 * cell_size), 2)
    
    # Горизонтальные линии
    for i in range(19):
        y = start_y + i * cell_size
        pygame.draw.line(board_surface, line_color, (start_x, y), (start_x + 18 * cell_size, y), 2)
    
    # Точки (хоси)
    hoshi_points = [3, 9, 15]
    for x_pos in hoshi_points:
        for y_pos in hoshi_points:
            if (x_pos in [3, 15] and y_pos in [3, 15]) or (x_pos == 9 and y_pos == 9):
                point_x = start_x + x_pos * cell_size
                point_y = start_y + y_pos * cell_size
                pygame.draw.circle(board_surface, line_color, (point_x, point_y), 4)
    
    # # Создаем тень доски
    # shadow_surface = pygame.Surface((board_width + 15, board_height + 15), pygame.SRCALPHA)
    # shadow_layers = [(0, 0, 60), (5, 5, 40), (10, 10, 20)]
    
    # for layer_offset_x, layer_offset_y, alpha in shadow_layers:
    #     shadow_color = (0, 0, 0, alpha)
    #     pygame.draw.rect(shadow_surface, shadow_color, 
    #                     (layer_offset_x, layer_offset_y, board_width, board_height))
    
    # # Рисуем тень и доску
    # screen.blit(shadow_surface, (delta_x + 15, delta_y + 15))
    screen.blit(board_surface, (delta_x, delta_y))

    return board_surface
    