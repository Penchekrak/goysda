from typing import Literal, NamedTuple

class Stone(NamedTuple):
    x: int
    y: int
    color: Literal['white', 'black']

class Cloud(NamedTuple):
    x: int
    y: int

class GameState:
    def __init__(self, config):
        self.placed_stones = [Stone(x=100, y=100, color='white'), Stone(x=200, y=200, color='black')]
        self.cloud_state = [Cloud(x=0, y=0)]

    def update(self, user_input):
        pass