from enum import Enum

from pygame.locals import QUIT, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, KEYDOWN, K_z, KMOD_LCTRL, KMOD_RCTRL, USEREVENT
from pygame.key import get_mods
import pygame_gui


class ActionType(Enum):
    """Типы действий в игре"""
    QUIT = 'quit'
    KEY_DOWN = 'key_down'
    MOUSE_DOWN_LEFT = 'mouse_down_left'
    MOUSE_DOWN_RIGHT = 'mouse_down_right'
    MOUSE_UP_LEFT = 'mouse_up_left'
    MOUSE_UP_RIGHT = 'mouse_up_right'
    MOUSE_MOTION = 'mouse_motion'
    MOUSE_SCROLL = 'mouse_scroll'
    UNDO = 'undo'
    FILEDIALOG_CONFIRMED = 'filedialog_confirmed'


def handle_input(events, xy_transformation_func):
    """
    Обрабатывает pygame события и возвращает словарь с действиями.
    Берет только последнее действие каждого типа события.
    
    Args:
        events: список pygame событий
        
    Returns:
        dict: словарь с действиями:
            - 'actions': list - список всех действий
    """
    # print(f"{len(user_inputs)=} | {user_inputs=}") # покликал, в массиве всегда один элемент поулчался! 
    # Но на всякий случай оставил список пусть будет. Для простоты логике вначале, будем считать, что в списке всегда одно действие.
    # Быстрым перемещением мыши получил два события: len(user_inputs)=2 | user_inputs=[{'action': 'mouse_motion', 'x': 160, 'y': 328, 'buttons': (1, 0, 0)}, {'action': 'mouse_motion', 'x': 161, 'y': 328, 'buttons': (1, 0, 0)}]
    # Будем считать что клик и отжатие только одно происходит, а перемещение можно последнее взять - тут без разницы! => берем только последнии события!
    
    actions = []  # Все действия для дебага
    total_move = {"action_type": ActionType.MOUSE_MOTION, "x": None, "y": None, "rel_x": 0, "rel_y": 0, "buttons": tuple()}

    for event in events:
        action = {}  # Словарь для хранения последних действий каждого типа
        if event.type == QUIT:
            action = {'action_type': ActionType.QUIT}
        
        elif event.type == MOUSEBUTTONDOWN:
            # Нажатие кнопки мыши
            if event.button == 1:  # левая кнопка
                action = {
                    'action_type': ActionType.MOUSE_DOWN_LEFT,
                    'button': 'left',
                    'x': event.pos[0],
                    'y': event.pos[1],
                }
            elif event.button == 3:  # правая кнопка
                action = {
                    'action_type': ActionType.MOUSE_DOWN_RIGHT,
                    'button': 'right', 
                    'x': event.pos[0],
                    'y': event.pos[1],
                }
            elif event.button == 4:
                action = {
                    'action_type': ActionType.MOUSE_SCROLL,
                    'x': event.pos[0],
                    'y': event.pos[1],
                    'value': 1,
                }
            elif event.button == 5:
                action = {
                    'action_type': ActionType.MOUSE_SCROLL,
                    'x': event.pos[0],
                    'y': event.pos[1],
                    'value': -1,
                }
        
        elif event.type == MOUSEBUTTONUP:
            # Отпускание кнопки мыши
            if event.button == 1:  # левая кнопка
                action = {
                    'action_type': ActionType.MOUSE_UP_LEFT,
                    'button': 'left',
                    'x': event.pos[0],
                    'y': event.pos[1]
                }
            elif event.button == 3:  # правая кнопка
                action = {
                    'action_type': ActionType.MOUSE_DOWN_RIGHT,
                    'button': 'right',
                    'x': event.pos[0],
                    'y': event.pos[1]
                }        
        elif event.type == MOUSEMOTION:
            total_move["x"] = event.pos[0]
            total_move["y"] = event.pos[1]
            total_move['rel_x'] += event.rel[0]
            total_move["rel_y"] += event.rel[1]
            total_move['buttons'] = tuple(set(total_move['buttons'] + event.buttons))  # (left, middle, right) - какие кнопки зажаты
        elif event.type == KEYDOWN:
            if event.key == K_z:
                action = {
                    'action_type': ActionType.UNDO
                }
            else:
                action = {
                    'action_type': ActionType.KEY_DOWN,
                    'key': event.key,
                }
        elif event.type == USEREVENT and event.user_type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
            action = {
                'action_type': ActionType.FILEDIALOG_CONFIRMED,
                'ui_element': event.ui_element,
                'text': event.text,
            }
        
        if "x" in action:
            action["x"], action["y"] = xy_transformation_func(action["x"], action["y"])
        if action:
            actions.append(action)
    
    if total_move["x"] is not None:
        total_move["x"], total_move["y"] = xy_transformation_func(total_move["x"], total_move["y"])
        total_move["rel_x"], total_move["rel_y"] = xy_transformation_func(total_move["rel_x"], total_move["rel_y"])
        actions.append(total_move)

    return actions


    

    