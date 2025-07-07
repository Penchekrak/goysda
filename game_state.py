from typing import Literal, NamedTuple, Tuple, Dict
from handle_input import ActionType
from utils import *
from snapper import snap_stone
from enum import Enum
import pygame
import shapely
import math


def snapping_mock(stone, list_of_stones):
    return stone


class Stone(NamedTuple):
    x: int
    y: int
    color: Literal['white', 'black', 'light_grey', 'dark_grey']



class PlacementsModes(Enum):
    nearest_possible = "Nearest possible"
    snap_to_my_color = "Snap to my color"
    snap_to_opponent_colors = "Snap to opponent color"
    

class GameState:
    def __init__(self, config):
        self.placed_stones = []
        self.player_to_move = 0
        self.background_state = 0
        self.suggestion_stone = None
        self.placement_modes = [0, 0]  # for each player his own mode
        self.territory_mode = [False, False]  # for each player his own mode
        self.suggestion_stone_color="black"
        self.voronoi_polygons = []
        self.voronoi_polygons_with_suggestion = []
        self.colors = ["black", "white"]
        self.territory = [0, 0]
        
        self.background_to_render = 'clouds'
        # self.background_to_render = 'water'
        
        self.board_to_render = 'limpid'
        # self.board_to_render = 'real'

        self.config = config
        delta_x, delta_y = calculate_deltax_deltay(config)
        self.board = shapely.Polygon([
            [delta_x, delta_y],
            [delta_x, delta_y + config['board_height']],
            [delta_x + config['board_width'], delta_y + config['board_height']],
            [delta_x + config['board_width'], delta_y]
        ])


    def update(self, user_input: Tuple[int, int, bool] = None):
        mouse_action = user_input.get(ActionType.MOUSE_DOWN_LEFT, {})
        if mouse_action:
            self.handle_click(mouse_action)
            self.handle_move(mouse_action)
        
        move_action = user_input.get(ActionType.MOUSE_MOTION, {})
        if move_action:
            self.handle_move(move_action)
        
        keyboard_action = user_input.get(ActionType.KEY_DOWN, {})
        if keyboard_action:
            self.handle_keydown(keyboard_action)

        self.background_state = (self.background_state + 1) % default_config['width']
    
    def handle_keydown(self, action):
        keyboard_digits = [pygame.K_1, pygame.K_2, pygame.K_3]
        if action["key"] == pygame.K_w:
            self.placement_modes[self.player_to_move] = (self.placement_modes[self.player_to_move] + 1) % len(PlacementsModes)
        elif action["key"] in keyboard_digits:
            self.placement_modes[self.player_to_move] = keyboard_digits.index(action["key"])
        elif action["key"] == pygame.K_b:
            self.background_to_render = 'clouds' if self.background_to_render == 'water' else 'water'
        elif action["key"] == pygame.K_n:
            self.board_to_render = 'real' if self.board_to_render == 'limpid' else 'limpid'
        elif action["key"] == pygame.K_t:
            self.territory_mode[self.player_to_move] = not self.territory_mode[self.player_to_move]


    def _snap_stone(self, x, y):
        mode = list(PlacementsModes)[self.placement_modes[self.player_to_move]]
        is_not_nearest_possible = (mode != PlacementsModes.nearest_possible)
        if ((self.player_to_move == 0) == (mode == PlacementsModes.snap_to_my_color)):
            snap_color = self.colors[0]
        else:
            snap_color = self.colors[1]

        return snap_stone(
            user_input=(x, y, is_not_nearest_possible), 
            game_state=self,
            game_config=default_config,
            snap_color=snap_color if is_not_nearest_possible else None,
        )
    
    def handle_move(self, action):
        x, y = self._snap_stone(action["x"], action["y"])
        self.suggestion_stone_color = ['dark_grey', 'light_grey'][self.player_to_move]
        self.suggestion_stone = Stone(x=x, y=y, color=self.suggestion_stone_color)
        self.calculate_voronoi_polygons()

    def handle_click(self, action):
        x, y = self._snap_stone(action["x"], action["y"])
        new_stone = Stone(x=x, y=y, color=self.colors[self.player_to_move])
        self.placed_stones.append(new_stone)

        current_player_color = self.colors[self.player_to_move]
        opponent_color = self.colors[(self.player_to_move + 1) % 2]
        kill_groups_of_color(opponent_color, self, default_config)
        kill_groups_of_color(current_player_color, self, default_config)
        
        self.player_to_move = (self.player_to_move + 1) % 2
        self.calculate_voronoi_polygons()
    
    def calculate_voronoi_polygons(self):
        if [self.suggestion_stone.x, self.suggestion_stone.y] in [[stone.x, stone.y] for stone in self.placed_stones]:
            self.suggestion_stone = Stone(self.suggestion_stone.x + 1, self.suggestion_stone.y, color=self.suggestion_stone_color)
        
        stones_list = self.placed_stones + [self.suggestion_stone]
        voronoi_polygons = shapely.voronoi_polygons(
            geometry=shapely.MultiPoint([[stone.x, stone.y] for stone in stones_list]),
            extend_to=self.board,
            ordered=True,
        ).geoms
        
        self.voronoi_polygons = [shapely.intersection(elem, self.board) for elem in voronoi_polygons]
        for i in range(len(self.colors)):
            if i == self.player_to_move:
                player_colors = [self.colors[i], self.suggestion_stone_color] 
            else:
                player_colors = [self.colors[i]]
            area_i = sum(elem.area * (stone.color in player_colors) for elem, stone in zip(self.voronoi_polygons, stones_list))
            self.territory[i] = round(area_i / (2 * math.pi * self.config["stone_radius"] ** 2), 2)

    def get_list_of_stones_to_draw(self):
        return ([] if not self.suggestion_stone else [self.suggestion_stone]) + self.placed_stones

    def get_list_of_shapes_to_draw(self):
        free_of_centers_zones, colors = [], []
        for stone, voro_poly in zip(self.placed_stones + [self.suggestion_stone], self.voronoi_polygons):
            border_indicator_stone = shapely.Point(stone.x, stone.y).buffer(self.config["stone_radius"] * 2)
            border_indicator_stone = shapely.intersection(border_indicator_stone, voro_poly)
            free_of_centers_zones.append(border_indicator_stone)
            if stone.color == self.suggestion_stone_color:
                colors.append(self.suggestion_stone_color)
            else:
                colors.append(["dark_grey", "light_grey"][stone.color == self.colors[1]])

        if not self.territory_mode[self.player_to_move]:
            return free_of_centers_zones, colors

        polygon_colors = []
        for stone in self.placed_stones:
            polygon_colors.append(["dark_grey_territory", "light_grey_territory"][stone.color == self.colors[1]])
        polygon_colors.append(["dark_grey_territory", "light_grey_territory"][self.player_to_move])
        return  self.voronoi_polygons, polygon_colors
    
    def get_info(self) -> Dict[str, str]:
        player_name = self.colors[self.player_to_move]
        return {
            "Player": player_name,
            "Player placement mode (toggle on W, 1, 2, 3)": f'{[elem.value for elem in PlacementsModes][self.placement_modes[self.player_to_move]]}',
            "Player territory mode (togle on T)": ["Don't show territory", "Show territory"][self.territory_mode[self.player_to_move]],
            "Black vs white": f"{self.territory[0]} - {self.territory[1]} ({round(self.territory[0] - self.territory[1], 5)})",
            "Toggle background on button": "B",
            "Toggle board on button": "N",
        }
