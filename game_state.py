from typing import Literal, NamedTuple, Tuple, Dict
from handle_input import ActionType
from utils import *
from snapper import snap_stone
from enum import Enum
import pygame
import shapely
import math


class Stone:
    x: int
    y: int
    color: Literal['white', 'black', 'light_grey', 'dark_grey']
    secondary_color: Literal['white', 'black', 'light_grey', 'dark_grey']

    def __init__(self, x, y, color, secondary_color=None):
        secondary_color = secondary_color or color
        self.x = x
        self.y = y
        self.color = color
        self.secondary_color = secondary_color
    
    def is_marked(self):
        return self.secondary_color != self.color
    
    def _as_dict(self):
        return {"x": self.x, "y": self.y, "color": self.color, "secondary_color": self.secondary_color}
    
    def __str__(self):
        return f"{self.__class__.__name__}(" + ", ".join(f"{key} = {value}" for key, value in self._as_dict().items()) + ")"
    
    __repr__ = __str__


class PlacementsModes(Enum):
    nearest_possible = "Nearest possible"
    snap_to_my_color = "Snap to my color"
    snap_to_opponent_colors = "Snap to opponent color"
    

class GameState:
    def __init__(self, config):
        self.placed_stones = []
        self.player_to_move = 0
        self.passes_counter = 0
        self.background_state = 0
        self.suggestion_stone = Stone(x=10**10, y=10**10, color="black_suggestion")
        self.placement_modes = [0, 0]  # for each player his own mode
        self.territory_mode = [False, False]  # for each player his own mode
        self.marking_dead_mode = [False, False]
        self.suggestion_stone_mode = [True, True]
        self.dont_show_suggestion_stone = False
    
        self.suggestion_stone_color="black"
        self.voronoi_polygons = []
        self.not_marked_as_dead_stones = []
        self.alive_voronoi_polygons = [] # voronoi polygons for the not_marked_as_dead stones
        self.colors = ["black", "white"]
        self.territory = [0, 0]
        self.moves_counter = 0

        self.background_to_render_list = ['clouds', 'water'] 
        self.background_to_render_index = 0 # background_to_render[0] is default, then change in order
        
        self.board_to_render_list = ['limpid', 'real']
        self.board_to_render_index = 1

        self.config = config
        delta_x, delta_y = calculate_deltax_deltay(config)
        self.board = shapely.Polygon([
            [delta_x, delta_y],
            [delta_x, delta_y + config['board_height']],
            [delta_x + config['board_width'], delta_y + config['board_height']],
            [delta_x + config['board_width'], delta_y]
        ])
        self.previous_move_action = {"x": 0, "y": 0}
        self.update(user_input=None)
    
    def is_the_game_over(self):
        return self.passes_counter >= 2
    
    def update(self, user_input):
        if user_input is None:
            self.handle_move()
            return
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
            self.handle_move()

        self.background_state = (self.background_state + 1) % default_config['width']
    
    def player_plays_pass(self):
        self.passes_counter += 1
        self.moves_counter += 1
        self.pass_the_turn()
    
    def pass_the_turn(self):
        self.player_to_move = (self.player_to_move + 1) % 2
        
    def handle_keydown(self, action):
        keyboard_digits = [pygame.K_1, pygame.K_2, pygame.K_3]
        if action["key"] == pygame.K_w:
            self.placement_modes[self.player_to_move] = (self.placement_modes[self.player_to_move] + 1) % len(PlacementsModes)
        elif action["key"] in keyboard_digits:
            self.placement_modes[self.player_to_move] = keyboard_digits.index(action["key"])
        elif action["key"] == pygame.K_b:
            self.background_to_render_index = (self.background_to_render_index + 1) % len(self.background_to_render_list)
        elif action["key"] == pygame.K_n:
            # self.board_to_render = 'real' if self.board_to_render == 'limpid' else 'limpid'
            self.board_to_render_index = (self.board_to_render_index + 1) % len(self.board_to_render_list)
        elif action["key"] == pygame.K_t:
            self.territory_mode[self.player_to_move] = not self.territory_mode[self.player_to_move]
        elif action["key"] == pygame.K_c:
            self.marking_dead_mode[self.player_to_move] = not self.marking_dead_mode[self.player_to_move]
        elif action["key"] == pygame.K_p:
            self.player_plays_pass()
        elif action["key"] == pygame.K_g:
            self.suggestion_stone_mode[self.player_to_move] = not self.suggestion_stone_mode[self.player_to_move]
        elif action["key"] == pygame.K_q:
            exit()

    def _snap_stone(self, x, y):
        mode = list(PlacementsModes)[self.placement_modes[self.player_to_move]]
        is_not_nearest_possible = (mode != PlacementsModes.nearest_possible)
        if ((self.player_to_move == 0) == (mode == PlacementsModes.snap_to_my_color)):
            snap_color = self.colors[0]
        else:
            snap_color = self.colors[1]

        if any(norm(x - stone.x, y - stone.y) ** 2 < (self.config["stone_radius"] / 5)**2 for stone in self.placed_stones):
            self.dont_show_suggestion_stone = True
            return None, None
        else:
            self.dont_show_suggestion_stone = False

        return snap_stone(
            user_input=(x, y, is_not_nearest_possible), 
            game_state=self,
            game_config=default_config,
            snap_color=snap_color if is_not_nearest_possible else None,
        )
    
    def handle_move(self, action=None):
        self.previous_move_action = action or self.previous_move_action
        x, y = self._snap_stone(self.previous_move_action["x"], self.previous_move_action["y"])
        self.suggestion_stone_color = self.colors[self.player_to_move] + "_suggestion"
        self.suggestion_stone = Stone(x=x, y=y, color=self.suggestion_stone_color)
        self.calculate_voronoi_polygons()
        self._calculate_territory()
    
    def placed_and_suggestion_stones(self):
        if self.is_the_game_over():
            return self.placed_stones
        if self.marking_dead_mode[self.player_to_move]:
            return self.placed_stones
        if not self.suggestion_stone_mode[self.player_to_move]:
            return self.placed_stones
        if self.dont_show_suggestion_stone:
            return self.placed_stones
        return self.placed_stones + [self.suggestion_stone]

    def handle_click(self, action):
        if self.is_the_game_over():
            return 
        
        if self.marking_dead_mode[self.player_to_move]:
            x, y = action["x"], action["y"]
            for stone_idx, stone in enumerate(self.placed_stones):
                if norm(stone.x - x, stone.y - y) <= self.config["stone_radius"] ** 2:
                    if stone.color == self.colors[self.player_to_move]:
                        selected_stone_idx = stone_idx
                        break
            else:
                return
            
            group_idx = compute_group(selected_stone_idx, self, self.config)
            for stone_idx in group_idx:
                self.placed_stones[stone_idx].secondary_color = get_opposite_color(self.placed_stones[stone_idx].secondary_color, self.colors)

            return

        self.passes_counter = 0
        self.moves_counter += 1
        x, y = self._snap_stone(action["x"], action["y"])
        new_stone = Stone(x=x, y=y, color=self.colors[self.player_to_move])
        self.placed_stones.append(new_stone)

        current_player_color = self.colors[self.player_to_move]
        opponent_color = self.colors[(self.player_to_move + 1) % 2]
        kill_groups_of_color(opponent_color, self, default_config)
        kill_groups_of_color(current_player_color, self, default_config)
        
        self.pass_the_turn()
        self.update_secondary_colors()
        self.calculate_voronoi_polygons()
    
    def update_secondary_colors(self):
        stone_groups = split_stones_by_groups(self, self.config)
        for stone_group in stone_groups:
            color_to_mark_group = None
            for stone_idx in stone_group:
                if self.placed_stones[stone_idx].is_marked():
                    color_to_mark_group = self.placed_stones[stone_idx].secondary_color
                    break
            if color_to_mark_group is not None:
                for stone_idx in stone_group:
                    self.placed_stones[stone_idx].secondary_color = color_to_mark_group

    def to_json(self):
        return {
            "stones": [stone._asdict() for stone in self.placed_stones],
            "moves_counter": self.moves_counter,
            "passes_counter": self.passes_counter,
            "is_marked_dead": self.is_marked_dead,
        }
    
    def new_from_json(self, json):
        new_gamestate = self.__class__(self.config)
        new_gamestate.placed_stones = [Stone(**stone_dict) for stone_dict in json["stones"]]
        new_gamestate.moves_counter = json["moves_counter"]
        new_gamestate.player_to_move = new_gamestate.moves_counter % 2
        new_gamestate.passes_counter = json["passes_counter"]
        new_gamestate.is_marked_dead = json.get("is_marked_dead", False)
        return new_gamestate

    def calculate_voronoi_polygons(self):
        if [self.suggestion_stone.x, self.suggestion_stone.y] in [[stone.x, stone.y] for stone in self.placed_stones]:
            self.suggestion_stone = Stone(self.suggestion_stone.x + 1, self.suggestion_stone.y, color=self.suggestion_stone_color)

        voronoi_polygons = shapely.voronoi_polygons(
            geometry=shapely.MultiPoint([[stone.x, stone.y] for stone in self.placed_and_suggestion_stones()]), #  
            extend_to=self.board,
            ordered=True,
        ).geoms
        self.voronoi_polygons = [shapely.intersection(elem, self.board) for elem in voronoi_polygons]

    def get_list_of_shapes_to_draw(self):
        self.update(user_input=None)
        if self.territory_mode[self.player_to_move]:
            return self._get_list_of_territory_polygons() + self._get_list_of_stones_to_draw()
        
        return self._get_list_of_border_zones() + self._get_list_of_border_stones() + self._get_list_of_connections() + self._get_list_of_stones_to_draw()

    def _get_list_of_territory_polygons(self):
        self._calculate_territory()
        polygon_colors = []
        for stone in self.not_marked_as_dead_stones:
            polygon_colors.append(stone.color + "_territory")

        rt = list(zip(self.alive_voronoi_polygons, polygon_colors)) 
        return rt

    def _get_list_of_stones_to_draw(self):
        rt = []
        r = self.config["stone_radius"]
        for stone in self.placed_and_suggestion_stones():
            x, y = stone.x, stone.y
            rt.append((shapely.Point(x, y).buffer(r), stone.color))
            rt.append((get_cross_polygon(x, y, (2**0.5) * r / 8, r / 16), stone.secondary_color))
        return rt            
    
    def _get_list_of_connections(self):
        connections = []
        edges_in_index_format = calculate_connections_graph(self, self.config)
        placed_and_suggestion_stones = self.placed_and_suggestion_stones()
        for edge in edges_in_index_format:
            stone1, stone2 = placed_and_suggestion_stones[edge[0]], placed_and_suggestion_stones[edge[1]]
            if stone1.color in self.colors and stone2.color in self.colors:
                if stone1.color != stone2.color:
                    continue
                else:
                    for elem in calculate_two_connection_polygons(stone1.x, stone1.y, stone2.x, stone2.y):
                        connections.append((elem, stone1.color + "_connection"))
            else:
                if stone1.color in self.colors:
                    stone1, stone2 = stone2, stone1
                if stone2.color != self.colors[self.player_to_move]:
                    continue
                for elem in calculate_two_connection_polygons(stone1.x, stone1.y, stone2.x, stone2.y):
                    connections.append((elem, stone2.color + "_connection_suggestion"))
        return connections

    def _get_list_of_border_stones(self):
        rt = []
        for stone, voro_poly in zip(self.placed_and_suggestion_stones(), self.voronoi_polygons):
            border_indicator_stone = shapely.Point(stone.x, stone.y).buffer(self.config["stone_radius"] * 2)
            border_indicator_stone = shapely.intersection(border_indicator_stone, voro_poly)
            if stone.color == self.suggestion_stone_color:
                rt.append((border_indicator_stone, self.suggestion_stone_color + "_border"))
            else:
                rt.append((border_indicator_stone, stone.color + "_border"))
        
        return rt

    def _get_list_of_border_zones(self):
        delta_x, delta_y = calculate_deltax_deltay(self.config)
        config = self.config
        w, h, r = config["board_width"], config["board_height"], config["stone_radius"]
        rectangles = [
            [[0, 0], [0, r], [w, r], [w, 0]],
            [[0, h], [0, h - r], [w, h - r], [w, h]],
            [[w - r, 0], [w, 0], [w, h], [w - r, h]],
            [[0, 0], [r, 0], [r, h], [0, h]],
        ]
        return [(shapely.Polygon([[x + delta_x, y + delta_y] for (x, y) in elem]), "board_border") for elem in rectangles]
    
    def _calculate_territory(self):
        self.not_marked_as_dead_stones = [stone for stone in self.placed_and_suggestion_stones() if not stone.is_marked()]
        self.alive_voronoi_polygons = shapely.voronoi_polygons(
            geometry=shapely.MultiPoint([[stone.x, stone.y] for stone in self.not_marked_as_dead_stones]), #  
            extend_to=self.board,
            ordered=True,
        ).geoms
        self.alive_voronoi_polygons = [shapely.intersection(elem, self.board) for elem in self.alive_voronoi_polygons]

        for i in range(len(self.colors)):
            if i == self.player_to_move:
                player_colors = [self.colors[i], self.suggestion_stone_color] 
            else:
                player_colors = [self.colors[i]]
            area_i = sum(elem.area * (stone.color in player_colors) for elem, stone in zip(self.alive_voronoi_polygons, self.not_marked_as_dead_stones))
            self.territory[i] = round(area_i / (4 * self.config["stone_radius"] ** 2), 2)

    def get_info(self) -> Dict[str, str]:
        player_name = self.colors[self.player_to_move]
        if self.is_the_game_over():
            if self.territory[0] >= self.territory[1] + 1:
                turn_info = {"Winner": self.colors[0]}
            elif self.territory[1] >= self.territory[0] + 1:
                turn_info = {"Winner": self.colors[1]}
            else:
                turn_info = {"Result": "tie"}
            print(f"Here {turn_info}")
        else:
            turn_info = {"Player": player_name}
        
        return turn_info | {
            "Player placement mode (toggle on W, 1, 2, 3)": f'{[elem.value for elem in PlacementsModes][self.placement_modes[self.player_to_move]]}',
            "Player territory mode           (togle on T)": ["Don't show territory", "Show territory"][self.territory_mode[self.player_to_move]],
            "Player ghost stone mode         (togle on G)": ["Hide ghost suggestion stone", "Show ghost suggestion stone"][self.suggestion_stone_mode[self.player_to_move]],
            "Player click mode               (togle on C)": ["Click means placing stones", "Click means marking dead groups"][self.marking_dead_mode[self.player_to_move]],
            "Black vs white": f"{self.territory[0]} - {self.territory[1]} ({round(self.territory[0] - self.territory[1], 5)})",
            # f"Toggle background on button ({self.background_to_render_list[self.background_to_render_index]})": "B",
            # f"Toggle board on button ({self.board_to_render_list[self.board_to_render_index]})": "N",
            # "For quit use": "Q",
        }
