from typing import Literal, NamedTuple, Tuple
from handle_input import ActionType
from utils import default_config
from snapper import snap_stone

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


    def update(self, user_input: Tuple[int, int, bool] = None):
        mouse_action = user_input.get(ActionType.MOUSE_DOWN_LEFT, {})
        if mouse_action:
            self.handle_click(mouse_action)
        
        move_action = user_input.get(ActionType.MOUSE_MOTION, {})
        if move_action:
            print(move_action)
            self.handle_move(move_action)
    
    def handle_move(self, action):
        x, y = action["x"], action["y"]
        x, y = snap_stone(
            user_input=(x, y, False), 
            game_state=self,
            game_config=default_config,
        )
        self.suggestion_stone = Stone(x=x, y=y, color=['light_grey', 'dark_grey'][self.player_to_move])

    def handle_click(self, action):
        x, y = action["x"], action["y"]
        x, y = snap_stone(
            user_input=(x, y, False), 
            game_state=self,
            game_config=default_config,
        )

        new_stone = Stone(x=x, y=y, color=['white', 'black'][self.player_to_move])
        self.placed_stones.append(new_stone)
        self.player_to_move = (self.player_to_move + 1) % 2
    
    def get_list_of_stones_to_draw(self):
        return ([] if not self.suggestion_stone else [self.suggestion_stone]) + self.placed_stones
