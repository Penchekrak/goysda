from typing import Literal, NamedTuple

class Stone(NamedTuple):
    x: int
    y: int
    color: Literal['white', 'black']

class GameState:
    def __init__(self):
        self.placed_stones = [Stone(x=100, y=100, color='white'), Stone(x=200, y=200, color='black')]

    def update(self, user_input):
        pass