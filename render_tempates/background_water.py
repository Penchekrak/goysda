import pygame
import numpy as np
import math

# Удаляем класс PreRenderedWater и связанные с ним импорты pickle и os

# Глобальные переменные для хранения последнего кадра и счетчика
last_water_surface = None
frame_counter = 0

def create_water_background(width, height, time):
    """Создаёт анимированный фон воды с эффектами как в shader репозитории"""
    # Создаём массивы координат
    x_coords = np.arange(width)
    y_coords = np.arange(height)
    X, Y = np.meshgrid(x_coords, y_coords)
    
    # Нормализуем координаты для UV
    U = X / width
    V = Y / height
    
    # Создаём волны как в шейдере - все множители времени теперь целые числа для идеального цикла
    wave1 = np.sin(U * 10.0 + time * 2.0) * 0.01
    wave2 = np.sin(V * 8.0 + time * 2.0) * 0.01 # Было 1.5
    wave3 = np.sin(U * 15.0 + V * 12.0 + time * 3.0) * 0.005
    
    # Применяем искажение к координатам
    distorted_U = U + wave1 + wave3
    distorted_V = V + wave2 + wave3
    
    # Базовый цвет воды (как в шейдере) - создаём для каждого пикселя
    water_color = np.zeros((height, width, 3))
    water_color[:, :, 0] = 0.2  # R
    water_color[:, :, 1] = 0.5  # G
    water_color[:, :, 2] = 0.8  # B
    
    # Добавляем вариации цвета
    noise = np.sin(distorted_U * 50.0 + time) * np.sin(distorted_V * 50.0 + time * 1.0) * 0.1 # Было 0.7
    water_color[:, :, 0] += noise * 0.1  # R
    water_color[:, :, 1] += noise * 0.05  # G
    water_color[:, :, 2] += noise * 0.2  # B
    
    # Градиент глубины
    depth = 1.0 - V * 0.3
    water_color *= depth[:, :, np.newaxis]
    
    # Добавляем блики
    highlight = np.sin(distorted_U * 20.0 + time * 4.0) * np.sin(distorted_V * 15.0 + time * 3.0) * 0.2
    water_color[:, :, 0] += highlight * 0.3  # R
    water_color[:, :, 1] += highlight * 0.2  # G
    water_color[:, :, 2] += highlight * 0.5  # B
    
    # Ограничиваем значения
    water_color = np.clip(water_color, 0, 1)
    
    # Конвертируем в RGB (0-255)
    water_color = (water_color * 255).astype(np.uint8)
    
    # Создаём поверхность pygame
    water_surface = pygame.Surface((width, height))
    
    # Конвертируем numpy массив в pygame поверхность
    pygame_surface_array = pygame.surfarray.make_surface(water_color)
    water_surface.blit(pygame_surface_array, (0, 0))
    
    return water_surface


# Удаляем старую реализацию с кешем
def render_water_background(screen, game_state, config):
    """
    Рендерит фон воды, обновляя его только каждый 3-й кадр для производительности.
    """
    global last_water_surface, frame_counter

    EVERY_N_PIXEL_CHANGE_RESULT = 5

    # Генерируем новый фон только каждый 3-й кадр (или если он еще не создан)
    if last_water_surface is None or frame_counter % EVERY_N_PIXEL_CHANGE_RESULT == 0:
        time = pygame.time.get_ticks() / 1000.0
        last_water_surface = create_water_background(config['width'], config['height'], time)

    # Отрисовываем последний сгенерированный фон
    screen.blit(last_water_surface, (0, 0))
    
    # Увеличиваем счетчик кадров
    frame_counter += 1


def create_water_background_with_params(width, height, time, 
                                      wave_speed=2.0, 
                                      wave_amplitude=0.01, 
                                      base_color=(0.2, 0.5, 0.8),
                                      noise_intensity=0.1,
                                      highlight_intensity=0.2):
    """Создаёт анимированный фон воды с настраиваемыми параметрами"""
    # Создаём массивы координат
    x_coords = np.arange(width)
    y_coords = np.arange(height)
    X, Y = np.meshgrid(x_coords, y_coords)
    
    # Нормализуем координаты для UV
    U = X / width
    V = Y / height
    
    # Создаём волны с настраиваемыми параметрами
    wave1 = np.sin(U * 10.0 + time * wave_speed) * wave_amplitude
    wave2 = np.sin(V * 8.0 + time * wave_speed * 0.75) * wave_amplitude
    wave3 = np.sin(U * 15.0 + V * 12.0 + time * wave_speed * 1.5) * wave_amplitude * 0.5
    
    # Применяем искажение к координатам
    distorted_U = U + wave1 + wave3
    distorted_V = V + wave2 + wave3
    
    # Базовый цвет воды с настраиваемыми параметрами
    water_color = np.zeros((height, width, 3))
    water_color[:, :, 0] = base_color[0]  # R
    water_color[:, :, 1] = base_color[1]  # G
    water_color[:, :, 2] = base_color[2]  # B
    
    # Добавляем вариации цвета
    noise = np.sin(distorted_U * 50.0 + time) * np.sin(distorted_V * 50.0 + time * 0.7) * noise_intensity
    water_color[:, :, 0] += noise * 0.1  # R
    water_color[:, :, 1] += noise * 0.05  # G
    water_color[:, :, 2] += noise * 0.2  # B
    
    # Градиент глубины
    depth = 1.0 - V * 0.3
    water_color *= depth[:, :, np.newaxis]
    
    # Добавляем блики с настраиваемой интенсивностью
    highlight = np.sin(distorted_U * 20.0 + time * 4.0) * np.sin(distorted_V * 15.0 + time * 3.0) * highlight_intensity
    water_color[:, :, 0] += highlight * 0.3  # R
    water_color[:, :, 1] += highlight * 0.2  # G
    water_color[:, :, 2] += highlight * 0.5  # B
    
    # Ограничиваем значения
    water_color = np.clip(water_color, 0, 1)
    
    # Конвертируем в RGB (0-255)
    water_color = (water_color * 255).astype(np.uint8)
    
    # Создаём поверхность pygame
    water_surface = pygame.Surface((width, height))
    
    # Конвертируем numpy массив в pygame поверхность
    pygame_surface_array = pygame.surfarray.make_surface(water_color)
    water_surface.blit(pygame_surface_array, (0, 0))
    
    return water_surface
