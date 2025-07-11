import sys
import pygame
import json
import utils
import copy 
import os
import asyncio

from pygame.locals import *
import pygame_gui
import shapely

from game_state import GameState
from rendering import render
from handle_input import handle_input, ActionType
from filedialog import FileDailog
from transformation import Transformation
import utils


if os.environ.get('PROFILING', '0') == '1':
    import pyinstrument

def main():
    actions_counter = 0
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
    delta_x, delta_y = utils.calculate_deltax_deltay(config)
    board = shapely.Polygon([[elem[0] + delta_x, elem[1] + delta_y] for elem in config["board_polygon"]])
    transformation = Transformation(0, 0, board)
    manager = pygame_gui.UIManager((config['width'], config['height']))
    filedialog = FileDailog(
        rect=pygame.Rect((0, 0), (config['width'], config['height'])),
        manager=manager,
    )

    game_state = GameState(config)
    game_states_stack = [copy.deepcopy(game_state)]
    if os.environ.get('PROFILING', '0') == '1':
        prof = None
    
    while True:
        if os.environ.get('PROFILING', '0') == '1':
            if len(game_state.placed_stones) == 50:
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
                with open(picked_path_of_none, "r") as f:
                    game_states_stack = [game_state.new_from_json(elem) for elem in json.load(f)]
                    game_state = copy.deepcopy(game_states_stack[-1])
            
            elif dialog_type_or_none == "save":
                with open(picked_path_of_none, "w") as f:
                    json.dump([elem.to_json() for elem in game_states_stack], f)
            
        
        for user_inputs in handle_input(pygame_events, transformation.screen_to_world):
            if ActionType.MOUSE_SCROLL in user_inputs:
                action = user_inputs[ActionType.MOUSE_SCROLL]
                transformation.update_self_zoom(action["x"], action["y"], config["zoom_speed"] * action["value"])
            if utils.is_control_pressed() or pygame.key.get_pressed()[pygame.K_LCTRL] and ActionType.MOUSE_MOTION in user_inputs: 
                action = user_inputs[ActionType.MOUSE_MOTION]
                transformation.update_self_drag(action["rel_x"], action["rel_y"])

            if ActionType.QUIT in user_inputs:
                pygame.quit()
                sys.exit()

            # filedialog
            for action_type, value in user_inputs.items():
                if action_type != ActionType.KEY_DOWN:
                    continue
                if value["key"] == pygame.K_r:
                    transformation.reset()
                if value["key"] == pygame.K_o:
                    filedialog.open_file_dialog("open")
                elif value["key"] == pygame.K_s:
                    filedialog.open_file_dialog("save")
                        
            if ActionType.UNDO in user_inputs:
                if len(game_states_stack) >= 2:
                    game_state = copy.deepcopy(game_states_stack[-2])
                    game_states_stack.pop()
                    actions_counter = game_state.actions_counter
                else:
                    print("Trying to undo empty position")
            
            # Update.
            if not filedialog.is_active():
                game_state.update(user_inputs)
            
            if actions_counter != game_state.actions_counter:
                game_states_stack.append(copy.deepcopy(game_state))
                actions_counter = game_state.actions_counter
        
        if os.environ.get('PROFILING', '0') == '1':
            if prof:
                prof.stop()
                prof.write_html('profile.html')
                prof = None
        
        game_state.update(None)
        game_state.update_background()

        render(screen, game_state, config, transformation)
        manager.update(1 / config['fps'])

        manager.draw_ui(screen)
        pygame.display.flip()
        fpsClock.tick(config['fps'])


if __name__ == "__main__":
    asyncio.run(main())