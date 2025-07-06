from pygame.locals import QUIT

def handle_input(events):
    for event in events:
        if event.type == QUIT:
            return 'quit'