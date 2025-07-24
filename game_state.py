from typing import Literal, NamedTuple, Tuple, Dict

import pygame
import shapely
import math

from handle_input import ActionType
from utils import *
from stones_structure import MyCache
from enum import Enum


class Stone:
    x: int
    y: int
    color: str
    secondary_color: str
    is_ko_attacker: bool

    def __init__(self, x, y, color, secondary_color=None, is_ko_attacker=False):
        self.x = x
        self.y = y
        self.color = color
        self.is_ko_attacker = is_ko_attacker
        self.update_secondary_color(secondary_color or color)
    
    def distance_squared(self, other):
        return distance_squared(self.x - other.x, self.y - other.y)

    def update_secondary_color(self, color=None):
        self.secondary_color = color or self.color
    
    def is_marked(self):
        return self.secondary_color != self.color
    
    def _asdict(self):
        return {"x": self.x, "y": self.y, "color": self.color, "secondary_color": self.secondary_color, "is_ko_attacker": self.is_ko_attacker}
    
    def __str__(self):
        return f"{self.__class__.__name__}(" + ", ".join(f"{key} = {value}" for key, value in self._asdict().items()) + ")"
    
    def __eq__(self, other):
        return self._asdict() == other._asdict()
    __repr__ = __str__


class PlacementsModes(Enum):
    nearest_possible = "Nearest possible"
    snap_to_my_color = "Snap to my color"
    snap_to_opponent_colors = "Snap to opponent color"
    

class GameState:
    def __init__(self, config, json=None):
        if json is not None:
            placed_stones = [Stone(**stone_dict) for stone_dict in json["stones"]]
            actions_counter=json["actions_counter"]
            player_to_move = json.get("player_to_move", json["actions_counter"] % 2)
            passes_counter= json["passes_counter"]
        else:
            placed_stones = []
            actions_counter = 0
            player_to_move = 0
            passes_counter = 0
        
        self.is_position_possible = True
        self.placed_stones = placed_stones
        self.player_to_move = player_to_move
        self.passes_counter = passes_counter
        self.background_state = 0
        self.suggestion_stone = Stone(x=10**10, y=10**10, color="black_suggestion")
        self.placement_modes = [0, 0]  # for each player his own mode
        self.territory_mode = [False, False]  # for each player his own mode
        self.marking_dead_mode = [False, False]
        self.suggestion_stone_mode = [True, True]
        self.dont_show_suggestion_stone = False
        self.fake_stone_mode = [False, False]
        self.fake_stones = [[], []]
        self.ko_stones = []

        self.not_marked_as_dead_stones = []
        self.colors = ["black", "white"]
        self.territory = [0, 0]
        self.actions_counter = actions_counter

        self.background_to_render_list = ['clouds', 'water'] 
        self.background_to_render_index = 0 # background_to_render[0] is default, then change in order
        
        self.board_to_render_list = ['limpid', 'real']
        self.board_to_render_index = 1

        self.config = config
        self.stone_radius = config["stone_radius"]

        delta_x, delta_y = calculate_deltax_deltay(config)
        self.board = shapely.Polygon([[delta_x + elem_x, delta_y + elem_y] for elem_x, elem_y in config["board_polygon"]]).normalize()
        self.board_inner = shapely.Polygon(shapely.intersection(self.board, self.board.exterior.buffer(self.stone_radius * (1 + 1e-4))).interiors[0]).normalize()
        self.previous_move_action = {"x": 0, "y": 0}
        
        self.cached_stone_structures = MyCache(stone_radius=self.stone_radius, board=self.board)
        self.update_placed_stone_structure()
        self.update_structure_for_snapping()
        self.update_preview_structure()
        self.update(action=None)
    
    def update_placed_stone_structure(self):
        self.cached_stone_structures.update("placed_stones", {"args": (remove_duplicate_stones(self.placed_stones),)})
    
    def update_structure_for_snapping(self):
        stones = remove_duplicate_stones(self.placed_stones + self._get_active_fake_stones())

        if self.is_the_game_over():
            stones = self.placed_stones
        self.cached_stone_structures.update("for_snapping", {"args": (stones,)})
    
    def update_preview_structure(self):
        stones = remove_duplicate_stones(self.placed_stones + self._get_list_of_0_or_1_suggestion_stones() + self._get_active_fake_stones())
        if self.is_the_game_over():
            stones = self.placed_stones
        try:
            self.cached_stone_structures.update("preview", {"args": (stones,)})
        except Exception as e:
            print(f"{self.player_to_move = }\n{self.previous_move_action['x'] = }, {self.previous_move_action['y'] = }\n{self.placed_stones = }\n{self._get_list_of_0_or_1_suggestion_stones() = }\n{self._get_active_fake_stones() = }\n{self.ko_stones = }\n")
            raise e
    
    def update_territory_structure(self):
        stones = remove_duplicate_stones([stone for stone in self.placed_stones if not stone.is_marked()] + self._get_list_of_0_or_1_suggestion_stones())
        if self.is_the_game_over():
            stones = self.placed_stones
        self.cached_stone_structures.update("territory", {"args": (stones,)})
            
    def update_suggestion_stone_status(self):
        if self.fake_stone_mode[self.player_to_move]:
            if "_hollow" not in self.suggestion_stone.color:
                self.suggestion_stone.color += "_hollow"
        else:
            if "_hollow" in self.suggestion_stone.color:
                self.suggestion_stone.color = self.suggestion_stone.color.replace("_hollow", "")
        self.suggestion_stone.update_secondary_color()

        x, y = self.previous_move_action["x"], self.previous_move_action["y"]
        if self.is_the_game_over():
            self.dont_show_suggestion_stone = True
        elif self.marking_dead_mode[self.player_to_move]:
            self.dont_show_suggestion_stone = True
        elif not self.suggestion_stone_mode[self.player_to_move]:
            self.dont_show_suggestion_stone = True
        elif index_of_stone_that_contains_a_point_or_none(x, y, self.placed_stones + self.fake_stones[self.player_to_move], self.stone_radius / 5) is not None:
            self.dont_show_suggestion_stone = True
        elif self.fake_stone_mode[self.player_to_move] and index_of_stone_that_contains_a_point_or_none(x, y, self.fake_stones[self.player_to_move], self.stone_radius) is not None:
            self.dont_show_suggestion_stone = True
        else:
            self.dont_show_suggestion_stone = False
    
    def _get_active_fake_stones(self):
        if self.is_the_game_over():
            return []
        return self.fake_stones[self.player_to_move]
        
    def _get_list_of_0_or_1_suggestion_stones(self):
        if self.dont_show_suggestion_stone:
            return []
        return [self.suggestion_stone]
            
    def is_the_game_over(self):
        return self.passes_counter >= 2
    
    def update(self, action):
        self.update_suggestion_stone_status()
        if action is None:
            self.handle_move()
            return

        if "x" in action:
            action["x"], action["y"] = project_point_onto_polygon(self.board_inner, shapely.Point(action["x"], action["y"])).coords[0]
            self.previous_move_action = action or self.previous_move_action
        
        self.update_suggestion_stone_status()
        if action["action_type"] in [ActionType.MOUSE_DOWN_LEFT, ActionType.MOUSE_DOWN_RIGHT]:
            self.handle_click(action, action["action_type"] == ActionType.MOUSE_DOWN_RIGHT)
        
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
        self.update_placed_stone_structure()
        self.update_preview_structure()
        self.update_structure_for_snapping()
        self.update_territory_structure()
        
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
        
        if self.dont_show_suggestion_stone:
            return None, None
        
        try:
            return self.cached_stone_structures.get_structure("for_snapping").calculate_snap_point(x, y, snap_color)
        except Exception as e:  
            print(f"{self.cached_stone_structures.get_structure("for_snapping").get_stones() = }")
            raise e
    
    def handle_move(self, action=None):
        x, y = self._snap_stone(self.previous_move_action["x"], self.previous_move_action["y"])
        self.suggestion_stone = Stone(x, y, self.colors[self.player_to_move] + "_suggestion")
        
        self.update_preview_structure()
        self.update_territory_structure()

        self._calculate_territory()
    
    def get_active_stones(self):
        # if self.is_the_game_over():
        #     return self.placed_stones
        # if self.marking_dead_mode[self.player_to_move]:
        #     return self.placed_stones
        # if not self.suggestion_stone_mode[self.player_to_move]:
        #     return self.placed_stones
        # if self.dont_show_suggestion_stone:
        #     return self.placed_stones + self.fake_stones[self.player_to_move]
        # if self.fake_stone_mode[self.player_to_move]:
        #     if "_hollow" not in self.suggestion_stone.color:
        #         self.suggestion_stone.color += "_hollow"

        # elif "_hollow" in self.suggestion_stone.color:
        #     self.suggestion_stone.color = self.suggestion_stone.color.replace("_hollow", "")
        # else:
        #     pass
        # self.suggestion_stone.update_secondary_color()

        # return self.placed_stones + [self.suggestion_stone] + self.fake_stones[self.player_to_move]
        return self.cached_stone_structures.get_structure("preview").get_stones()

    def handle_click(self, action, is_right_button_pressed=False):
        if self.is_the_game_over():
            return 
        
        if self.marking_dead_mode[self.player_to_move]:
            x, y = action["x"], action["y"]
            stone_of_player_color = [stone for stone in self.placed_stones if self.colors[self.player_to_move] in stone.color]
            selected_stone_idx = index_of_stone_that_contains_a_point_or_none(x, y, stone_of_player_color, self.stone_radius)
            if selected_stone_idx is None:
                return
            
            group_idx = compute_group(selected_stone_idx, stone_of_player_color, self.config)
            for stone_idx in group_idx:
                if "_suggestion" not in stone_of_player_color[stone_idx].color:
                    stone_of_player_color[stone_idx].secondary_color = get_opposite_color(stone_of_player_color[stone_idx].secondary_color, self.colors)
            
            self.actions_counter += 1
            self.update_territory_structure()
            return
        
        if self.fake_stone_mode[self.player_to_move]:
            self.actions_counter += 1
            selected_fake_stone_idx = index_of_stone_that_contains_a_point_or_none(action["x"], action["y"], self.fake_stones[self.player_to_move], self.stone_radius)
            if selected_fake_stone_idx is not None:
                self.fake_stones[self.player_to_move].pop(selected_fake_stone_idx)
            else:
                x, y = self._snap_stone(action["x"], action["y"])
                if x is None:
                    return
                
                color = self.colors[self.player_to_move] + "_hollow"
                if is_right_button_pressed:
                    color = get_opposite_color(color, self.colors)
                new_fake_stone = Stone(x=x, y=y, color=color)
                self.fake_stones[self.player_to_move].append(new_fake_stone)
            
            self.dont_show_suggestion_stone = True
            
            self.update_structure_for_snapping()
            self.update_preview_structure()
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

        self.update_placed_stone_structure()
        killed_opponent_stones = self._kill_groups_of_color(opponent_color)
        for stone in self.placed_stones:
            stone.is_ko_attacker = False
        if len(killed_opponent_stones) == 1:
            if killed_opponent_stones[0].is_ko_attacker:
                self.is_position_possible = False
            else:
                self.placed_stones[-1].is_ko_attacker = True

        self.update_placed_stone_structure()
        killed_player_stones = self._kill_groups_of_color(current_player_color)
        if new_stone in killed_player_stones:
            self.is_position_possible = False
                    
        self.pass_the_turn()
        self.update_secondary_colors()

        self.dont_show_suggestion_stone = True 
        self.update_placed_stone_structure()
        self.update_preview_structure()
        self.update_structure_for_snapping()
    
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
            "player_to_move": self.player_to_move,
            "passes_counter": self.passes_counter,
        }

    def get_list_of_shapes_to_draw(self):
        polygons_list = []
        for polygon_or_multipolygon, color in self._get_list_of_shapes_to_draw():
            if type(polygon_or_multipolygon) == shapely.Polygon:
                polygons_list.append((polygon_or_multipolygon, color))
            elif type(polygon_or_multipolygon) == shapely.MultiPolygon:
                polygons_list.extend([(polygon, color) for polygon in polygon_or_multipolygon.geoms])
            # else:
            #     print(type(polygon_or_multipolygon))
            #     raise NotImplementedError
        
        polygons_list2 = []
        for polygon, color in polygons_list:
            if "_hollow" in color:
                color = color.replace("_hollow", "")
                polygon_exterior_thicked = shapely.intersection(polygon.exterior.buffer(self.config["line_width"]), polygon)
                if type(polygon_exterior_thicked) in [shapely.Polygon, shapely.MultiPolygon]:
                    polygons_list2.append((remove_interior_if_it_exists(polygon_exterior_thicked), color))
            else:
                polygons_list2.append((polygon, color))
        return polygons_list2
    
    def _get_list_of_shapes_to_draw(self):
        self.update(action=None)
        if self.territory_mode[self.player_to_move]:
            return self._get_list_of_territory_polygons() + self._get_list_of_stones_to_draw()
        
        return self._get_list_of_border_zones() + self._get_list_of_border_stones() + self._get_list_of_connections() + self._get_list_of_stones_to_draw() + self._get_list_of_librety_highliters()

    def _kill_groups_of_color(self, color):
        groups = split_stones_by_groups(self.placed_stones, self.config)
        indexes_of_stones_to_kill = []

        for group in groups:
            if self.placed_stones[group[0]].color == color:
                if not group_has_librety(group, self.cached_stone_structures.get_structure("placed_stones")):
                    # TODO: add KO rule etc
                    indexes_of_stones_to_kill += group
        stones_to_kill = [self.cached_stone_structures.get_structure("placed_stones")[i] for i in indexes_of_stones_to_kill]
        self._kill_group(indexes_of_stones_to_kill)
        return stones_to_kill
    
    def _kill_group(self, group):
        self.placed_stones = [s for i, s in enumerate(self.placed_stones) if i not in group]
    
    def _get_list_of_territory_polygons(self):
        self._calculate_territory()
        
        territory_structure = self.cached_stone_structures.get_structure("territory")
        rt = list(zip(territory_structure.get_voronoi_polygons(), [elem.color.replace("_hollow", "") + "_territory" for elem in territory_structure.get_stones()])) 
        return rt

    def _get_list_of_librety_highliters(self):
        rt = []
        preview_structure = self.cached_stone_structures.get_structure("preview")
        small_libreties_for_hightlighting = preview_structure.get_small_librety_intervals_in_xy_format(self.config["minimal_librety_angle_to_hightlight"])
        for i in range(preview_structure._n):
            stone_i = preview_structure[i]
            for xy_start, xy_end in small_libreties_for_hightlighting[i]:
                rt.append((shapely.Polygon([[stone_i.x, stone_i.y], xy_start, xy_end]).buffer(self.stone_radius / 20), stone_i.color.replace("_hollow", "") + "_small_librety"))
        return rt
        
    def _get_list_of_stones_to_draw(self):
        rt = []
        for stone in self.get_active_stones():
            x, y = stone.x, stone.y
            rt.append((shapely.Point(x, y).buffer(self.stone_radius), stone.color))
            if stone.is_marked():
                rt.append((get_cross_polygon(x, y, (2**0.5) * self.stone_radius / 8, self.stone_radius / 16), stone.secondary_color))
            
            if stone.is_ko_attacker:
                rt.append((get_k_polygon(x, y, self.stone_radius / 2, self.stone_radius / 10), "grey")) # , self.stone_radius / 10, self.stone_radius / 2 ** 1.5
        if self.marking_dead_mode[self.player_to_move]:
            if self.previous_move_action:
                x, y = self.previous_move_action["x"], self.previous_move_action["y"]
                rt.append((get_cross_polygon(x, y, (2**0.5) * self.stone_radius / 8, self.stone_radius / 16), get_opposite_color(self.suggestion_stone.color, self.colors)))
        

        return rt            
    
    def _get_list_of_connections(self):
        connections = []
        active_stones = self.get_active_stones()
        edges_in_index_format = self.cached_stone_structures.get_structure("preview").calculate_connections_graph()
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
        voronoi_polygons = self.cached_stone_structures.get_structure("preview").get_voronoi_polygons()
        for stone, voro_poly in zip(self.get_active_stones(), voronoi_polygons):
            border_indicator_stone = shapely.Point(stone.x, stone.y).buffer(self.stone_radius * 2)
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
        alive_voronoi_polygons = self.cached_stone_structures.get_structure("territory").get_voronoi_polygons()

        for i in range(len(self.colors)):
            if i == self.player_to_move:
                player_colors = [self.colors[i], self.suggestion_stone.color] 
            else:
                player_colors = [self.colors[i]]
            area_i = sum(elem.area * (stone.color in player_colors) for elem, stone in zip(alive_voronoi_polygons, self.not_marked_as_dead_stones))
            self.territory[i] = round(area_i / (4 * self.stone_radius ** 2), 2)
        self.territory[1] += self.config["komi"]

    def get_info(self) -> Dict[str, str]:
        player_name = self.colors[self.player_to_move]
        territory_info = {"Black vs white": f"{self.territory[0]} - {self.territory[1]} ({round(self.territory[0] - self.territory[1], 5)})"}
        if self.is_the_game_over():
            if self.territory[0] >= self.territory[1] + 1:
                rt = {"Winner": self.colors[0]}
            elif self.territory[1] >= self.territory[0] + 1:
                rt = {"Winner": self.colors[1]}
            else:
                rt = {"Result": "tie"}
            return rt | territory_info
                
        return {
            "Player": player_name
        } | territory_info | {
            "Player placement mode    (toggle on W, 1, 2, 3)": f'{[elem.value for elem in PlacementsModes][self.placement_modes[self.player_to_move]]}',
            "Player territory mode              (togle on T)": ["Don't show territory", "Show territory"][self.territory_mode[self.player_to_move]],
            "Player ghost stone mode            (togle on G)": ["Hide ghost suggestion stone", "Show ghost suggestion stone"][self.suggestion_stone_mode[self.player_to_move]],
            "Player fake stones mode            (togle on F)": ["Off", "On"][self.fake_stone_mode[self.player_to_move]],
            "Player marking groups as dead mode (togle on X)": ["Click means placing stones", "Click means marking dead groups"][self.marking_dead_mode[self.player_to_move]],
            # f"Toggle background on button ({self.background_to_render_list[self.background_to_render_index]})": "B",
            # f"Toggle board on button ({self.board_to_render_list[self.board_to_render_index]})": "N",
        }
