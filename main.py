import pygame
import sys
from pygame.locals import *
from game_state import GameState
from rendering import render
from handle_input import handle_input, ActionType
import json
import utils
import copy 
import os
if os.environ.get('PROFILING', '0') == '1':
    import pyinstrument

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
    game_states_stack = [copy.deepcopy(game_state)]
    if os.environ.get('PROFILING', '0') == '1':
        prof = None
    # Game loop.
    while True:
        if os.environ.get('PROFILING', '0') == '1':
            if len(game_state.placed_stones) == 50:
                prof = pyinstrument.Profiler()
                prof.start()
        user_inputs = handle_input(pygame.event.get())
        user_inputs = user_inputs['last_actions']
        print(f"{user_inputs=}")

        if ActionType.QUIT in user_inputs:
            pygame.quit()
            sys.exit()

        if ActionType.UNDO in user_inputs:
            print(f"UNDO")
            game_state = copy.deepcopy(game_states_stack[-2])
            game_states_stack.pop()
        
        # Update.
        game_state.update(user_inputs)
        if ActionType.MOUSE_DOWN_LEFT in user_inputs or ActionType.MOUSE_DOWN_RIGHT in user_inputs:
            game_states_stack.append(copy.deepcopy(game_state))
        
        if os.environ.get('PROFILING', '0') == '1':
            if prof:
                prof.stop()
                prof.write_html('profile.html')
                prof = None

        # Draw.
        render(screen, game_state, config)
        pygame.display.flip()
        fpsClock.tick(config['fps'])