from pygame.locals import QUIT, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION

def handle_input(events):
    """
    Обрабатывает pygame события и возвращает словарь с действиями.
    Берет только последнее действие каждого типа события.
    
    Args:
        events: список pygame событий
        
    Returns:
        dict: словарь с действиями:
            - 'all_actions': list - все действия для дебага
            - 'last_actions': dict - последние действия каждого типа с ключами:
                - 'quit': {'action': 'quit'} - выход из игры
                - 'mouse_down_left': {'action': 'mouse_down', 'button': 'left', 'x': int, 'y': int}
                - 'mouse_down_right': {'action': 'mouse_down', 'button': 'right', 'x': int, 'y': int}
                - 'mouse_up_left': {'action': 'mouse_up', 'button': 'left', 'x': int, 'y': int}
                - 'mouse_up_right': {'action': 'mouse_up', 'button': 'right', 'x': int, 'y': int}
                - 'mouse_motion': {'action': 'mouse_motion', 'x': int, 'y': int, 'buttons': tuple}
                  где buttons = (left, middle, right) - 1 если зажата, 0 если нет
    """
    # print(f"{len(user_inputs)=} | {user_inputs=}") # покликал, в массиве всегда один элемент поулчался! 
    # Но на всякий случай оставил список пусть будет. Для простоты логике вначале, будем считать, что в списке всегда одно действие.
    # Быстрым перемещением мыши получил два события: len(user_inputs)=2 | user_inputs=[{'action': 'mouse_motion', 'x': 160, 'y': 328, 'buttons': (1, 0, 0)}, {'action': 'mouse_motion', 'x': 161, 'y': 328, 'buttons': (1, 0, 0)}]
    # Будем считать что клик и отжатие только одно происходит, а перемещение можно последнее взять - тут без разницы! => берем только последнии события!
    
    actions = []  # Все действия для дебага
    last_actions = {}  # Словарь для хранения последних действий каждого типа
    
    for event in events:
        if event.type == QUIT:
            action = {'action': 'quit'}
            actions.append(action)
            last_actions['quit'] = action
        
        elif event.type == MOUSEBUTTONDOWN:
            # Нажатие кнопки мыши
            if event.button == 1:  # левая кнопка
                action = {
                    'action': 'mouse_down',
                    'button': 'left',
                    'x': event.pos[0],
                    'y': event.pos[1]
                }
                actions.append(action)
                last_actions['mouse_down_left'] = action
            elif event.button == 3:  # правая кнопка
                action = {
                    'action': 'mouse_down',
                    'button': 'right', 
                    'x': event.pos[0],
                    'y': event.pos[1]
                }
                actions.append(action)
                last_actions['mouse_down_right'] = action
        
        elif event.type == MOUSEBUTTONUP:
            # Отпускание кнопки мыши
            if event.button == 1:  # левая кнопка
                action = {
                    'action': 'mouse_up',
                    'button': 'left',
                    'x': event.pos[0],
                    'y': event.pos[1]
                }
                actions.append(action)
                last_actions['mouse_up_left'] = action
            elif event.button == 3:  # правая кнопка
                action = {
                    'action': 'mouse_up',
                    'button': 'right',
                    'x': event.pos[0],
                    'y': event.pos[1]
                }
                actions.append(action)
                last_actions['mouse_up_right'] = action
        
        elif event.type == MOUSEMOTION:
            # Движение мыши
            action = {
                'action': 'mouse_motion',
                'x': event.pos[0],
                'y': event.pos[1],
                'buttons': event.buttons  # (left, middle, right) - какие кнопки зажаты
            }
            actions.append(action)
            last_actions['mouse_motion'] = action
    
    # Возвращаем словарь с полной информацией
    return {
        'all_actions': actions,
        'last_actions': last_actions
    }


    

    