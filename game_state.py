from typing import Literal, NamedTuple, Tuple



def snapping_mock(stone, list_of_stones):
    return stone


class Stone(NamedTuple):
    x: int
    y: int
    color: Literal['white', 'black']


class GameState:
    def __init__(self):
        self.placed_stones = []
        self.player_to_move = 0

    def update(self, user_input: Tuple[int, int, bool]):
        x, y, is_magnet = user_input
        new_stone = Stone(x=x, y=y, color=['white', 'black'][self.player_to_move])
        new_stone = snapping_mock(new_stone, self.placed_stones)
        self.placed_stones.append(new_stone)
        self.player_to_move = (self.player_to_move + 1) % 2
    

