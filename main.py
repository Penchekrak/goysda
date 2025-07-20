import asyncio
import sys
import json
import utils
import copy 
import os

import pygame
from pygame.locals import *
import pygame_gui
import shapely

from game_history import GameStateHistory
from rendering import render
from handle_input import handle_input, ActionType
from filedialog import FileDailog
from transformation import Transformation
import utils


if os.environ.get('PROFILING', '0') == '1':
    import pyinstrument

def main():
    config = {}
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        with open(config_path, 'r') as f:
            config = json.load(f)
    config.update(utils.default_config)
    utils.update_colors(config=config)

    pygame.init()
    
    fpsClock = pygame.time.Clock()
    
    screen = pygame.display.set_mode((config['width'], config['height']))
    pygame.display.set_caption(config['window title'])

    delta_x, delta_y = utils.calculate_deltax_deltay(config)
    board = shapely.Polygon([[elem[0] + delta_x, elem[1] + delta_y] for elem in config["board_polygon"]])
    transformation = Transformation(0, 0, shapely.convex_hull(board))
    manager = pygame_gui.UIManager((config['width'], config['height']))
    filedialog = FileDailog(
        rect=pygame.Rect((0, 0), (config['width'], config['height'])),
        manager=manager,
    )

    game_history = GameStateHistory(config)
    if os.environ.get('PROFILING', '0') == '1':
        prof = None
    
    while True:
        if os.environ.get('PROFILING', '0') == '1':
            if len(game_state.placed_stones) == 200:
                prof = pyinstrument.Profiler()
                prof.start()
        
        pygame_events = pygame.event.get()
        for pygame_event in pygame_events:
            manager.process_events(pygame_event)
            dialog_type_or_none, picked_path_of_none = filedialog.handle_event(pygame_event)
            if dialog_type_or_none is None:
                continue

            transformation.reset()
            if dialog_type_or_none == "open":
                game_history.open_from_a_file(picked_path_of_none)
            
            elif dialog_type_or_none == "save":
                game_history.save_to_file(picked_path_of_none)
            
        for action in handle_input(pygame_events, transformation.screen_to_world):
            if action["action_type"] == ActionType.MOUSE_SCROLL:
                transformation.update_self_zoom(action["x"], action["y"], config["zoom_speed"] * action["value"])
                continue

            if utils.is_control_pressed() and action["action_type"] == ActionType.MOUSE_MOTION: 
                transformation.update_self_drag(action["rel_x"], action["rel_y"])

            if action["action_type"] == ActionType.QUIT:
                pygame.quit()
                sys.exit()

            # filedialog
            if action["action_type"] == ActionType.KEY_DOWN:
                if action["key"] == pygame.K_r:
                    transformation.reset()
                if action["key"] == pygame.K_o:
                    filedialog.open_file_dialog("open")
                elif action["key"] == pygame.K_s:
                    filedialog.open_file_dialog("save")
            
            if not filedialog.is_active():
                game_history.update(action)
        
        if os.environ.get('PROFILING', '0') == '1':
            if prof:
                prof.stop()
                prof.write_html('profile.html')
                prof = None
        
        game_history.update(None)
        game_history.current_game_state.update_background()

        render(screen, game_history.current_game_state, config, transformation)
        manager.update(1 / config['fps'])

        manager.draw_ui(screen)
        pygame.display.flip()
        fpsClock.tick(config['fps'])


if __name__ == "__main__":
    asyncio.run(main())