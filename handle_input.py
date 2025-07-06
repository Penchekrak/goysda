from pygame.locals import QUIT, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION

def handle_input(events):
    """
    Обрабатывает pygame события и возвращает список действий.
    
    Args:
        events: список pygame событий
        
    Returns:
        list: список словарей с действиями:
        
        - QUIT: {'action': 'quit'} - выход из игры
        - MOUSEBUTTONDOWN: {'action': 'mouse_down', 'button': 'left'|'right', 'x': int, 'y': int} - нажатие кнопки мыши
        - MOUSEBUTTONUP: {'action': 'mouse_up', 'button': 'left'|'right', 'x': int, 'y': int} - отпускание кнопки мыши  
        - MOUSEMOTION: {'action': 'mouse_motion', 'x': int, 'y': int, 'buttons': tuple} - движение мыши
          где buttons = (left, middle, right) - 1 если зажата, 0 если нет
    """
    actions = []
    
    for event in events:
        if event.type == QUIT:
            actions.append({'action': 'quit'})
        
        elif event.type == MOUSEBUTTONDOWN:
            # Нажатие кнопки мыши
            if event.button == 1:  # левая кнопка
                actions.append({
                    'action': 'mouse_down',
                    'button': 'left',
                    'x': event.pos[0],
                    'y': event.pos[1]
                })
            elif event.button == 3:  # правая кнопка
                actions.append({
                    'action': 'mouse_down',
                    'button': 'right', 
                    'x': event.pos[0],
                    'y': event.pos[1]
                })
        
        elif event.type == MOUSEBUTTONUP:
            # Отпускание кнопки мыши
            if event.button == 1:  # левая кнопка
                actions.append({
                    'action': 'mouse_up',
                    'button': 'left',
                    'x': event.pos[0],
                    'y': event.pos[1]
                })
            elif event.button == 3:  # правая кнопка
                actions.append({
                    'action': 'mouse_up',
                    'button': 'right',
                    'x': event.pos[0],
                    'y': event.pos[1]
                })
        
        elif event.type == MOUSEMOTION:
            # Движение мыши
            actions.append({
                'action': 'mouse_motion',
                'x': event.pos[0],
                'y': event.pos[1],
                'buttons': event.buttons  # (left, middle, right) - какие кнопки зажаты
            })
    
    return actions


    

    