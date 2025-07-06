from typing import Literal, NamedTuple, Tuple, Dict
from handle_input import ActionType
from utils import *
from snapper import snap_stone
import pygame


def snapping_mock(stone, list_of_stones):
    return stone


class Stone(NamedTuple):
    x: int
    y: int
    color: Literal['white', 'black', 'light_grey', 'dark_grey']

class Cloud(NamedTuple):
    x: int
    y: int


class GameState:
    def __init__(self, config):
        self.placed_stones = []
        self.player_to_move = 0
        self.cloud_state = [Cloud(x=0, y=0)]
        self.suggestion_stone = None
        self.placement_modes = [0, 0] # for each player his own mode


    def update(self, user_input: Tuple[int, int, bool] = None):
        mouse_action = user_input.get(ActionType.MOUSE_DOWN_LEFT, {})
        if mouse_action:
            self.handle_click(mouse_action)
        
        move_action = user_input.get(ActionType.MOUSE_MOTION, {})
        if move_action:
            self.handle_move(move_action)
        
        keyboard_action = user_input.get(ActionType.KEY_DOWN, {})
        if keyboard_action:
            self.handle_keydown(keyboard_action)
    
    def handle_keydown(self, action):
        if action["key"] == pygame.K_w:
            self.placement_modes[self.player_to_move] = (self.placement_modes[self.player_to_move] + 1) % 2
    
    def _snap_stone(self, x, y):
        return snap_stone(
            user_input=(x, y, self.placement_modes[self.player_to_move]), 
            game_state=self,
            game_config=default_config,
            snap_color=('black' if self.player_to_move % 2 == 0 else 'white')
        )
    
    def handle_move(self, action):
        x, y = self._snap_stone(action["x"], action["y"])
        self.suggestion_stone = Stone(x=x, y=y, color=['dark_grey', 'light_grey'][self.player_to_move])

    def handle_click(self, action):
        x, y = self._snap_stone(action["x"], action["y"])
        new_stone = Stone(x=x, y=y, color=['black', 'white'][self.player_to_move])
        self.placed_stones.append(new_stone)
        current_player_color = ('black' if self.player_to_move % 2 == 0 else 'white')
        opponent_color = ('white' if self.player_to_move % 2 == 0 else 'black')
        kill_groups_of_color(opponent_color, self, default_config)
        kill_groups_of_color(current_player_color, self, default_config)
        self.player_to_move = (self.player_to_move + 1) % 2
    
    def get_list_of_stones_to_draw(self):
        return ([] if not self.suggestion_stone else [self.suggestion_stone]) + self.placed_stones
    
    def get_info(self) -> Dict[str, str]:
        player_name = ["black", "white"][self.player_to_move]
        return {
            "Player": player_name,
            f"Mode ({player_name})": ["nearest possible", "magnet"][self.placement_modes[self.player_to_move]]
        }
