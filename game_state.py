from typing import Literal, NamedTuple, Tuple, Dict

import pygame
import shapely
import math

from handle_input import ActionType
from utils import *
from snapper import snap_stone
from stones_structure import StoneStructure
from enum import Enum


class Stone:
    x: int
    y: int
    color: str
    secondary_color: str

    def __init__(self, x, y, color, secondary_color=None):
        self.x = x
        self.y = y
        self.color = color
        self.update_secondary_color(secondary_color or color)
    
    def distance_squared(self, other):
        return distance_squared(self.x - other.x, self.y - other.y)

    def update_secondary_color(self, color=None):
        self.secondary_color = color or self.color
    
    def is_marked(self):
        return self.secondary_color != self.color
    
    def _asdict(self):
        return {"x": self.x, "y": self.y, "color": self.color, "secondary_color": self.secondary_color}
    
    def __str__(self):
        return f"{self.__class__.__name__}(" + ", ".join(f"{key} = {value}" for key, value in self._asdict().items()) + ")"
    
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
        self.fake_stone_mode = [False, False]
        self.fake_stones = [[], []]

        self.voronoi_polygons = []
        self.not_marked_as_dead_stones = []
        self.alive_voronoi_polygons = [] # voronoi polygons for the not_marked_as_dead stones
        self.colors = ["black", "white"]
        self.territory = [0, 0]
        self.actions_counter = 0

        self.background_to_render_list = ['clouds', 'water'] 
        self.background_to_render_index = 0 # background_to_render[0] is default, then change in order
        
        self.board_to_render_list = ['limpid', 'real']
        self.board_to_render_index = 1

        self.config = config
        delta_x, delta_y = calculate_deltax_deltay(config)
        self.board = shapely.Polygon([[delta_x + elem_x, delta_y + elem_y] for elem_x, elem_y in config["board_polygon"]]).normalize()
        self.board_inner = shapely.Polygon(shapely.intersection(self.board, self.board.exterior.buffer(self.config["stone_radius"] * (1 + 1e-4))).interiors[0]).normalize()
        self.previous_move_action = {"x": 0, "y": 0}
        self.recalculate_active_stones_structure()
        self.update(action=None)
    
    def recalculate_active_stones_structure(self):
        stones_to_struct = [stone for stone in self.get_active_stones() if "_suggestion" not in stone.color]
        self.active_not_suggestion_stones_structure = StoneStructure(stones_to_struct, self.config["stone_radius"], self.board)
    
    def is_the_game_over(self):
        return self.passes_counter >= 2
    
    def update(self, action):
        if action is None:
            self.handle_move()
            return

        if "x" in action:
            action["x"], action["y"] = project_point_onto_polygon(self.board_inner, shapely.Point(action["x"], action["y"])).coords[0]
        if action["action_type"] == ActionType.MOUSE_DOWN_LEFT:
            self.handle_click(action)
        
        if action["action_type"] == ActionType.MOUSE_MOTION:
            self.handle_move(action)
        
        if action["action_type"] == ActionType.KEY_DOWN:
            self.handle_keydown(action)
            self.handle_move()

    def update_background(self):
        self.background_state = (self.background_state + 1) % default_config['width']
    
    def player_plays_pass(self):
        self.passes_counter += 1
        self.actions_counter += 1
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
        elif action["key"] == pygame.K_x:
            self.marking_dead_mode[self.player_to_move] = not self.marking_dead_mode[self.player_to_move]
        elif action["key"] == pygame.K_p:
            self.player_plays_pass()
        elif action["key"] == pygame.K_g:
            self.suggestion_stone_mode[self.player_to_move] = not self.suggestion_stone_mode[self.player_to_move]
        elif action["key"] == pygame.K_f:
            self.fake_stone_mode[self.player_to_move] = not self.fake_stone_mode[self.player_to_move]
        elif action["key"] == pygame.K_q:
            exit()

    def _snap_stone(self, x, y):
        mode = list(PlacementsModes)[self.placement_modes[self.player_to_move]]
        if mode == PlacementsModes.nearest_possible:
            snap_color = None
        else:
            if ((self.player_to_move == 0) == (mode == PlacementsModes.snap_to_my_color)):
                snap_color = self.colors[0]
            else:
                snap_color = self.colors[1]
        
        bad_stone_idx_or_none = index_of_stone_that_contains_a_point_or_none(x, y, self.placed_stones, self.config["stone_radius"] / 5)
        if bad_stone_idx_or_none is not None:
            # self.dont_show_suggestion_stone = True
            # return None, None
            x += 0.000000000001              
        elif self.fake_stone_mode[self.player_to_move] and index_of_stone_that_contains_a_point_or_none(x, y, self.fake_stones[self.player_to_move], self.config["stone_radius"]) is not None:
            self.dont_show_suggestion_stone = True
            return None, None
        else:
            self.dont_show_suggestion_stone = False
        
        return self.active_not_suggestion_stones_structure.calculate_snap_point(x, y, snap_color)
    
    def handle_move(self, action=None):
        self.previous_move_action = action or self.previous_move_action
        x, y = self._snap_stone(self.previous_move_action["x"], self.previous_move_action["y"])
        self.suggestion_stone = Stone(x, y, self.colors[self.player_to_move] + "_suggestion")
        self.calculate_voronoi_polygons()
        self._calculate_territory()
    
    def get_active_stones(self):
        if self.is_the_game_over():
            return self.placed_stones
        if self.marking_dead_mode[self.player_to_move]:
            return self.placed_stones
        if not self.suggestion_stone_mode[self.player_to_move]:
            return self.placed_stones
        if self.dont_show_suggestion_stone:
            return self.placed_stones + self.fake_stones[self.player_to_move]
        if self.fake_stone_mode[self.player_to_move]:
            if "_hollow" not in self.suggestion_stone.color:
                self.suggestion_stone.color += "_hollow"

        elif "_hollow" in self.suggestion_stone.color:
            self.suggestion_stone.color = self.suggestion_stone.color.replace("_hollow", "")
        else:
            pass
        self.suggestion_stone.update_secondary_color()

        return self.placed_stones + [self.suggestion_stone] + self.fake_stones[self.player_to_move]

    def handle_click(self, action):
        if self.is_the_game_over():
            return 
        
        if self.marking_dead_mode[self.player_to_move]:
            x, y = action["x"], action["y"]
            stone_of_player_color = [stone for stone in self.placed_stones if self.colors[self.player_to_move] in stone.color]
            selected_stone_idx = index_of_stone_that_contains_a_point_or_none(x, y, stone_of_player_color, self.config["stone_radius"])
            if selected_stone_idx is None:
                return
            
            group_idx = compute_group(selected_stone_idx, stone_of_player_color, self.config)
            for stone_idx in group_idx:
                if "_suggestion" not in stone_of_player_color[stone_idx].color:
                    stone_of_player_color[stone_idx].secondary_color = get_opposite_color(stone_of_player_color[stone_idx].secondary_color, self.colors)
            
            self.actions_counter += 1
            return
        
        if self.fake_stone_mode[self.player_to_move]:
            self.actions_counter += 1
            selected_fake_stone_idx = index_of_stone_that_contains_a_point_or_none(action["x"], action["y"], self.fake_stones[self.player_to_move], self.config["stone_radius"])
            if selected_fake_stone_idx is not None:
                self.fake_stones[self.player_to_move].pop(selected_fake_stone_idx)
                self.recalculate_active_stones_structure()
                return
            
            x, y = self._snap_stone(action["x"], action["y"])
            if x is None:
                return
            
            new_fake_stone = Stone(x=x, y=y, color=self.colors[self.player_to_move] + "_hollow")
            self.fake_stones[self.player_to_move].append(new_fake_stone)
            self.recalculate_active_stones_structure()
            return

        x, y = self._snap_stone(action["x"], action["y"])
        if x is None:
            return
        
        self.passes_counter = 0
        self.actions_counter += 1

        new_stone = Stone(x=x, y=y, color=self.colors[self.player_to_move])
        self.placed_stones.append(new_stone)

        current_player_color = self.colors[self.player_to_move]
        opponent_color = self.colors[(self.player_to_move + 1) % 2]

        killed_stones = self._kill_groups_of_color(opponent_color)
        self._kill_groups_of_color(current_player_color)
        
        self.pass_the_turn()
        self.recalculate_active_stones_structure()
        self.update_secondary_colors()
        self.calculate_voronoi_polygons()
    
    def update_secondary_colors(self):
        stone_groups = split_stones_by_groups(self.placed_stones, self.config)
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
            "actions_counter": self.actions_counter,
            "passes_counter": self.passes_counter,
        }
    
    def new_from_json(self, json):
        new_gamestate = self.__class__(self.config)
        new_gamestate.placed_stones = [Stone(**stone_dict) for stone_dict in json["stones"]]
        new_gamestate.actions_counter = json["actions_counter"]
        new_gamestate.player_to_move = new_gamestate.actions_counter % 2
        new_gamestate.passes_counter = json["passes_counter"]
        new_gamestate.is_marked_dead = json.get("is_marked_dead", False)
        new_gamestate.recalculate_active_stones_structure()
        return new_gamestate

    def calculate_voronoi_polygons(self):
        if [self.suggestion_stone.x, self.suggestion_stone.y] in [[stone.x, stone.y] for stone in self.placed_stones]:
            self.suggestion_stone = Stone(self.suggestion_stone.x + 1, self.suggestion_stone.y, color=self.suggestion_stone.color)

        voronoi_polygons = shapely.voronoi_polygons(
            geometry=shapely.MultiPoint([[stone.x, stone.y] for stone in self.get_active_stones()]), #  
            extend_to=self.board,
            ordered=True,
        ).geoms
        self.voronoi_polygons = [shapely.intersection(elem, self.board) for elem in voronoi_polygons]

    def get_list_of_shapes_to_draw(self):
        self.update(action=None)
        if self.territory_mode[self.player_to_move]:
            return self._get_list_of_territory_polygons() + self._get_list_of_stones_to_draw()
        
        return self._get_list_of_border_zones() + self._get_list_of_border_stones() + self._get_list_of_connections() + self._get_list_of_stones_to_draw()

    def _kill_groups_of_color(self, color, recalculate_stones_structure=True):
        stones_sturcture = StoneStructure(self.placed_stones, self.config["stone_radius"], self.board)
        groups = split_stones_by_groups(self.placed_stones, self.config)
        stones_to_kill = []

        for group in groups:
            if self.placed_stones[group[0]].color == color:
                if not group_has_librety(group, stones_sturcture):
                    # TODO: add KO rule etc
                    stones_to_kill += group
        self._kill_group(stones_to_kill)
        return len(stones_to_kill)
    
    def _kill_group(self, group):
        self.placed_stones = [s for i, s in enumerate(self.placed_stones) if i not in group]
    
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
        for stone in self.get_active_stones():
            x, y = stone.x, stone.y
            rt.append((shapely.Point(x, y).buffer(r), stone.color))
            if stone.is_marked():
                rt.append((get_cross_polygon(x, y, (2**0.5) * r / 8, r / 16), stone.secondary_color))
        if self.marking_dead_mode[self.player_to_move]:
            if self.previous_move_action:
                x, y = self.previous_move_action["x"], self.previous_move_action["y"]
                rt.append((get_cross_polygon(x, y, (2**0.5) * r / 8, r / 16), get_opposite_color(self.suggestion_stone.color, self.colors)))
        
        for i in range(self.active_not_suggestion_stones_structure._n):
            x, y = self.active_not_suggestion_stones_structure[i].x, self.active_not_suggestion_stones_structure[i].y
            for angles in self.active_not_suggestion_stones_structure._librety_intervals_in_angle_format[i]:
                angles = list(angles)
                if angles[0] is None:
                    angles[0] = -math.pi
                if angles[1] is None:
                    angles[1] = math.pi
                for angle in angles:
                    xy = x + self.config["stone_radius"] * 2 * math.cos(angle), y + self.config["stone_radius"] * 2 * math.sin(angle)
                    rt.append((shapely.Polygon(thicken_a_line_segment(xy[0], xy[1], x, y, 3)), "red"))
        return rt            
    
    def _get_list_of_connections(self):
        connections = []
        active_stones = self.get_active_stones()
        edges_in_index_format = StoneStructure(active_stones, self.config["stone_radius"], self.board_inner, dont_calculate_dame=True).calculate_connections_graph()
        for edge in edges_in_index_format:
            stone1, stone2 = active_stones[edge[0]], active_stones[edge[1]]
            hollow_suffix = "_hollow" if ("_hollow" in stone1.color or "_hollow" in stone2.color) else ""

            stone1_color, stone2_color = stone1.color.replace("_hollow", ""), stone2.color.replace("_hollow", "")
            if "_suggestion" not in stone1_color and "_suggestion" not in stone2_color:
                if stone1_color == stone2_color:
                    connection = calculate_connection_polygon(stone1.x, stone1.y, stone2.x, stone2.y)
                    connections.append((connection, stone1_color + "_connection" + hollow_suffix))
            else:
                if "_suggestion" in stone2_color:
                    stone1, stone2 = stone2, stone1
                    stone1_color, stone2_color = stone2_color, stone1_color

                if self.colors[self.player_to_move] in stone2_color: # drawing connections only to the players stones
                    connection = calculate_connection_polygon(stone1.x, stone1.y, stone2.x, stone2.y)
                    connections.append((connection, stone2_color + "_connection_suggestion" + hollow_suffix))
        return connections

    def _get_list_of_border_stones(self):
        rt = []
        for stone, voro_poly in zip(self.get_active_stones(), self.voronoi_polygons):
            border_indicator_stone = shapely.Point(stone.x, stone.y).buffer(self.config["stone_radius"] * 2)
            border_indicator_stone = shapely.intersection(border_indicator_stone, voro_poly)
            if stone.color == self.suggestion_stone.color:
                rt.append((border_indicator_stone, self.suggestion_stone.color + "_border"))
            else:
                rt.append((border_indicator_stone, stone.color + "_border"))
        
        return rt

    def _get_list_of_border_zones(self):
        delta_x, delta_y = calculate_deltax_deltay(self.config)
        return [
            (self.board, "board_border"),
            (self.board_inner, "board")
        ]

    def _calculate_territory(self):
        self.not_marked_as_dead_stones = [stone for stone in self.get_active_stones() if not stone.is_marked() and not "_hollow" in stone.color]
        self.alive_voronoi_polygons = shapely.voronoi_polygons(
            geometry=shapely.MultiPoint([[stone.x, stone.y] for stone in self.not_marked_as_dead_stones]), #  
            extend_to=self.board,
            ordered=True,
        ).geoms
        self.alive_voronoi_polygons = [shapely.intersection(elem, self.board) for elem in self.alive_voronoi_polygons]

        for i in range(len(self.colors)):
            if i == self.player_to_move:
                player_colors = [self.colors[i], self.suggestion_stone.color] 
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
        else:
            turn_info = {"Player": player_name}
        
        return turn_info | {
            "Player placement mode (toggle on W, 1, 2, 3)": f'{[elem.value for elem in PlacementsModes][self.placement_modes[self.player_to_move]]}',
            "Player territory mode           (togle on T)": ["Don't show territory", "Show territory"][self.territory_mode[self.player_to_move]],
            "Player ghost stone mode         (togle on G)": ["Hide ghost suggestion stone", "Show ghost suggestion stone"][self.suggestion_stone_mode[self.player_to_move]],
            "Player click mode               (togle on X)": ["Click means placing stones", "Click means marking dead groups"][self.marking_dead_mode[self.player_to_move]],
            "Black vs white": f"{self.territory[0]} - {self.territory[1]} ({round(self.territory[0] - self.territory[1], 5)})",
            # f"Toggle background on button ({self.background_to_render_list[self.background_to_render_index]})": "B",
            # f"Toggle board on button ({self.board_to_render_list[self.board_to_render_index]})": "N",
            # "For quit use": "Q",
        }
