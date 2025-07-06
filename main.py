import pygame
import sys
from pygame.locals import *
from game_state import GameState
from rendering import render
from handle_input import handle_input
import json
import utils

if __name__ == "__main__":
    config = {}
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        with open(config_path, 'r') as f:
            config = json.load(f)
    config.update(utils.default_config)

    pygame.init()
    
    fpsClock = pygame.time.Clock()
    
    screen = pygame.display.set_mode((config['width'], config['height']))

    game_state = GameState(config)
    # Game loop.
    while True:

        user_inputs = handle_input(pygame.event.get())
        # print(f"{len(user_inputs)=} | {user_inputs=}") # покликал, в массиве всегда один элемент поулчался! 
        # Но на всякий случай оставил список пусть будет. Для простоты логике вначале, будем считать, что в списке всегда одно действие.
        # Быстрым перемещением мыши получил два события: len(user_inputs)=2 | user_inputs=[{'action': 'mouse_motion', 'x': 160, 'y': 328, 'buttons': (1, 0, 0)}, {'action': 'mouse_motion', 'x': 161, 'y': 328, 'buttons': (1, 0, 0)}]
        if 'quit' in [user_input['action'] for user_input in user_inputs]:
            pygame.quit()
            sys.exit()

        # Update.
        game_state.update(user_inputs)
        # Draw.
        render(screen, game_state, config)
        pygame.display.flip()
        fpsClock.tick(config['fps'])