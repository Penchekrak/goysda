from enum import Enum

from pygame.locals import QUIT, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, KEYDOWN, K_z, KMOD_LCTRL, KMOD_RCTRL, USEREVENT
from pygame.key import get_mods
import pygame_gui

import utils


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
            - 'all_actions': list - все действия для дебага
            - 'last_actions': dict - последние действия каждого типа с ключами ActionType:
                - ActionType.QUIT: {'action': 'quit'} - выход из игры
                - ActionType.MOUSE_DOWN_LEFT: {'action': 'mouse_down', 'button': 'left', 'x': int, 'y': int}
                - ActionType.MOUSE_DOWN_RIGHT: {'action': 'mouse_down', 'button': 'right', 'x': int, 'y': int}
                - ActionType.MOUSE_UP_LEFT: {'action': 'mouse_up', 'button': 'left', 'x': int, 'y': int}
                - ActionType.MOUSE_UP_RIGHT: {'action': 'mouse_up', 'button': 'right', 'x': int, 'y': int}
                - ActionType.MOUSE_MOTION: {'action': 'mouse_motion', 'x': int, 'y': int, 'buttons': tuple}
                  где buttons = (left, middle, right) - 1 если зажата, 0 если нет
    """
    # print(f"{len(user_inputs)=} | {user_inputs=}") # покликал, в массиве всегда один элемент поулчался! 
    # Но на всякий случай оставил список пусть будет. Для простоты логике вначале, будем считать, что в списке всегда одно действие.
    # Быстрым перемещением мыши получил два события: len(user_inputs)=2 | user_inputs=[{'action': 'mouse_motion', 'x': 160, 'y': 328, 'buttons': (1, 0, 0)}, {'action': 'mouse_motion', 'x': 161, 'y': 328, 'buttons': (1, 0, 0)}]
    # Будем считать что клик и отжатие только одно происходит, а перемещение можно последнее взять - тут без разницы! => берем только последнии события!
    
    actions = []  # Все действия для дебага
    total_move = {"action": "mouse_motion", "x": None, "y": None, "rel_x": 0, "rel_y": 0, "buttons": tuple()}

    for event in events:
        last_actions = {}  # Словарь для хранения последних действий каждого типа
        if event.type == QUIT:
            action = {'action': 'quit'}
            last_actions[ActionType.QUIT] = action
        
        elif event.type == MOUSEBUTTONDOWN:
            # Нажатие кнопки мыши
            if event.button == 1:  # левая кнопка
                action = {
                    'action': 'mouse_down',
                    'button': 'left',
                    'x': event.pos[0],
                    'y': event.pos[1],
                    'is_cntrl_pressed': utils.is_control_pressed(),
                }
                last_actions[ActionType.MOUSE_DOWN_LEFT] = action
            elif event.button == 3:  # правая кнопка
                action = {
                    'action': 'mouse_down',
                    'button': 'right', 
                    'x': event.pos[0],
                    'y': event.pos[1],
                    'is_cntrl_pressed': utils.is_control_pressed(),
                }
                last_actions[ActionType.MOUSE_DOWN_RIGHT] = action
            elif event.button == 4:
                action = {
                    'action': 'mouse_scroll',
                    'x': event.pos[0],
                    'y': event.pos[1],
                    'value': 1,
                }
                last_actions[ActionType.MOUSE_SCROLL] = action
            elif event.button == 5:
                action = {
                    'action': 'mouse_scroll_up',
                    'x': event.pos[0],
                    'y': event.pos[1],
                    'value': -1,
                }
                last_actions[ActionType.MOUSE_SCROLL] = action
        
        elif event.type == MOUSEBUTTONUP:
            # Отпускание кнопки мыши
            if event.button == 1:  # левая кнопка
                action = {
                    'action': 'mouse_up',
                    'button': 'left',
                    'x': event.pos[0],
                    'y': event.pos[1]
                }
                last_actions[ActionType.MOUSE_UP_LEFT] = action
            elif event.button == 3:  # правая кнопка
                action = {
                    'action': 'mouse_up',
                    'button': 'right',
                    'x': event.pos[0],
                    'y': event.pos[1]
                }
                last_actions[ActionType.MOUSE_UP_RIGHT] = action
        
        elif event.type == MOUSEMOTION:
            total_move["x"] = event.pos[0]
            total_move["y"] = event.pos[1]
            total_move['rel_x'] += event.rel[0]
            total_move["rel_y"] += event.rel[1]
            total_move['buttons'] = tuple(set(total_move['buttons'] + event.buttons))  # (left, middle, right) - какие кнопки зажаты
        elif event.type == KEYDOWN:
            if event.key == K_z:
                action = {
                    'action': 'undo'
                }
                last_actions[ActionType.UNDO] = action
            else:
                action = {
                    'action': 'key_down',
                    'key': event.key,
                }
                last_actions[ActionType.KEY_DOWN] = action
        elif event.type == USEREVENT and event.user_type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
            action = {
                'action': 'user_event',
                'ui_element': event.ui_element,
                'text': event.text,
            }
            last_actions[ActionType.FILEDIALOG_CONFIRMED] = action
        
        for value in last_actions.values():
            if "x" in value:
                value["x"], value["y"] = xy_transformation_func(value["x"], value["y"])
        actions.append(last_actions)
    
    if total_move["x"] is not None:
        total_move["x"], total_move["y"] = xy_transformation_func(total_move["x"], total_move["y"])
        total_move["rel_x"], total_move["rel_y"] = xy_transformation_func(total_move["rel_x"], total_move["rel_y"])
        actions.append({ActionType.MOUSE_MOTION: total_move})

    return actions


    

    