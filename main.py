import pygame
import sys
from pygame.locals import *
from game_state import GameState
from rendering import render
from handle_input import handle_input, ActionType
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
        user_inputs = user_inputs['last_actions']

        if ActionType.QUIT in user_inputs:
            pygame.quit()
            sys.exit()
        
        # Update.
        game_state.update(user_inputs)
        # Draw.
        render(screen, game_state, config)
        pygame.display.flip()
        fpsClock.tick(config['fps'])