from typing import Literal, NamedTuple, Tuple
from handle_input import ActionType
from utils import default_config
from snapper import snap_stone

def snapping_mock(stone, list_of_stones):
    return stone


class Stone(NamedTuple):
    x: int
    y: int
    color: Literal['white', 'black']

class Cloud(NamedTuple):
    x: int
    y: int


class GameState:
    def __init__(self, config):
        self.placed_stones = []
        self.player_to_move = 0
        self.cloud_state = [Cloud(x=0, y=0)]


    def update(self, user_input: Tuple[int, int, bool] = None):
        action = user_input.get(ActionType.MOUSE_DOWN_LEFT, {})
        if not action:
            return 

        x, y = action["x"], action["y"]
        x, y = snap_stone(
            user_input=(x, y, False), 
            game_state=self,
            game_config=default_config,
        )
        new_stone = Stone(x=x, y=y, color=['white', 'black'][self.player_to_move])
        self.placed_stones.append(new_stone)
        self.player_to_move = (self.player_to_move + 1) % 2

