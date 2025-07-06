import pygame
import sys
from pygame.locals import *
from game_state import GameState
from rendering import render
from handle_input import handle_input
 

if __name__ == "__main__":

    pygame.init()
    
    fps = 60
    fpsClock = pygame.time.Clock()
    
    width, height = 480, 480
    screen = pygame.display.set_mode((width, height))

    game_state = GameState()
    # Game loop.
    while True:

        user_input = handle_input(pygame.event.get())
        
        if user_input == 'quit':
            pygame.quit()
            sys.exit()

        # Update.
        game_state.update(user_input)
        # Draw.
        render(screen, game_state)
        pygame.display.flip()
        fpsClock.tick(fps)