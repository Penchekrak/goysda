from collections import defaultdict
from functools import lru_cache

import copy
import math 
import random
import shapely

from utils import argmin, find_uncovered_arcs, thicken_a_line_segment, distance_squared, index_of_stone_that_contains_a_point_or_none


class StoneStructure:
    def __init__(self, stones, stone_radius, board):
        self._n = len(stones)
        self._stones = list(stones)
        self._stone_radius = stone_radius
        self._board = board
        self._board_coords = list(board.boundary.coords)
        self._board_border_circles = [(*elem, self._stone_radius * (1 + 1e-5)) for elem in self._board_coords]
        self._board_border_rectangles = []
        for i in range(len(self._board_coords) - 1):
            v1, v2 = self._board_coords[i], self._board_coords[i + 1]
            self._board_border_rectangles.append(thicken_a_line_segment(*v1, *v2, self._stone_radius * (1 + 1e-5)))
        
        self._delone_neighbours = defaultdict(list)
        self._delone_edges_ind = []
        self._voronoi_polygons = []
        self._recalculate_delone_graph()
        self._calculate_librety_intervals()
    
    def get_stones(self):
        return self._stones
    
    def _recalculate_delone_graph(self):
        points = shapely.MultiPoint([[stone.x + 1e-15 * random.random(), stone.y + 1e-15*random.random()] for stone in self._stones]) # 1e-15 is unfortunately needed, due to the bug underneath
        point_to_index = {point: i for i, point in enumerate(points.geoms)}
        delone_edges = shapely.delaunay_triangles(points, only_edges=True).geoms
        delone_edges_ind = []
        for edge in delone_edges:
            p1, p2 = edge.boundary.geoms
            ind1, ind2 = point_to_index[p1], point_to_index[p2]
            delone_edges_ind.append((ind1, ind2) if ind1 < ind2 else (ind2, ind1))
        self._delone_edges_ind = list(set(delone_edges_ind))
        delone_neighbours = defaultdict(list)
        for v1, v2 in self._delone_edges_ind:
            delone_neighbours[v1].append(v2)
            delone_neighbours[v2].append(v1)
        
        self._delone_neighbours = delone_neighbours
        
        voronoi_polygons = shapely.voronoi_polygons(points, extend_to=self._board, ordered=True)
        self._voronoi_polygons = [shapely.intersection(pol, self._board) for pol in voronoi_polygons.geoms]
    
    def get_voronoi_polygons(self):
        return self._voronoi_polygons
    
    def calculate_connections_graph(self, tolerance=1e-5):
        return [[ind1, ind2] for ind1, ind2 in self._delone_edges_ind
                 if self._stones[ind1].distance_squared(self._stones[ind2]) <= (2 * self._stone_radius + tolerance)**2]
    
    def calculate_all_vertexes_within_distance(self, stone_ind, distance):
        rt_list = [stone_ind]
        rt_set = {stone_ind}
        ind = 0
        while ind < len(rt_list):
            cur_ind = rt_list[ind]
            for neigbour_ind in self._delone_neighbours[cur_ind]:
                if neigbour_ind not in rt_set and self._stones[stone_ind].distance_squared(self._stones[cur_ind]) <= distance ** 2:
                    rt_list.append(neigbour_ind)
                    rt_set.add(neigbour_ind)
            ind += 1
        
        return rt_list
    
    def __getitem__(self, ind):
        return self._stones[ind]
    
    def __len__(self):
        return self._n
    
    def _ind_to_circle(self, ind):
        return (self._stones[ind].x, self._stones[ind].y, 2 * self._stone_radius)
 
    def _calculate_librety_intervals(self):
        """
        Assignes _librety_intervals to the list[list[(int, int)]] where i-the element contains list of intervals that are uncovered by board border and other stones borders for the i-th stone.
        self._librety_intervals_in_angle_format: list[(int, int)] stores list of pairs (angles of the start of the interval, angle of the end of interval).
        self._librety_intervals_in_xy_format: list[((int, int), (int, int))] stores stores list of pairs of pairs ((x coord of the start of the interval, y coord of the start of the interval, ), (...same for the end of the interval...))
        """
        #print("Called _calculate_librety_intervals")

        self._librety_intervals_in_angle_format = [(-1, -1)] * self._n
        self._librety_intervals_in_xy_format = [[] for _ in range(self._n)]
        for ind in range(self._n):            
            # print(f"{ind = }")
            stone_circ = self._ind_to_circle(ind)
            stone_neighb = [self._ind_to_circle(neighb_ind) for neighb_ind in self.calculate_all_vertexes_within_distance(ind, 4 * self._stone_radius + 1e-5)]
            stone_neighb = stone_neighb[1:] # removing ind-th stone from his neighbours
            if self._n > 2 and not stone_neighb:
                print("!" * 50, 4 * self._stone_radius + 1e-5, [math.sqrt(distance_squared(self._stones[ind].x - stone.x, self._stones[ind].y - stone.y)) for stone in self._stones])
                print(self.calculate_all_vertexes_within_distance(ind, 4 * self._stone_radius + 1e-5))

            librety_intervals = find_uncovered_arcs(stone_circ, stone_neighb + self._board_border_circles, self._board_border_rectangles, alpha=1e-20, epsilon=0) # angle format
            self._librety_intervals_in_angle_format[ind] = librety_intervals
            for angle_start, angle_end in librety_intervals:
                cur_xy = (
                    (self._stones[ind].x + 2 * self._stone_radius * math.cos(angle_start), self._stones[ind].y + 2 * self._stone_radius * math.sin(angle_start)),
                    (self._stones[ind].x + 2 * self._stone_radius * math.cos(angle_end), self._stones[ind].y + 2 * self._stone_radius * math.sin(angle_end))
                )
                self._librety_intervals_in_xy_format[ind].append(cur_xy)
            
            # print(f"{ind = }")
            # print(f"circle = {(self._stones[ind].x, self._stones[ind].y, 2 * self._stone_radius)}")
            # print(f"circles = {stone_neighb}")
            # print(f"candidate_points = {sum(self._librety_intervals_in_xy_format[ind], tuple())}")
            # print(f"polygons = {self._board_border_rectangles}")
            # print(f"board_board_circles = {self._board_border_circles}")
            # print()
    
    def get_small_librety_intervals_in_xy_format(self, threshold_alpha):
        rt = [[] for _ in range(self._n)]
        for i in range(self._n):
            for (angle_start, angle_end), (xy_start, xy_end) in zip(self._librety_intervals_in_angle_format[i], self._librety_intervals_in_xy_format[i]):
                if angle_end - angle_start > threshold_alpha:
                    continue
                rt[i].append((xy_start, xy_end))

        return rt
    
    def has_liberty_in_direction(self, stone_ind: int, angle: float) -> bool:
        angle = angle % (2 * math.pi)
        if angle > math.pi:
            angle -= 2 * math.pi
        # print(f"has_liberty_in_direction: {angle = }, {self._librety_intervals_in_angle_format[stone_ind] = }", end = " ")
        for interval_start, interval_end in self._librety_intervals_in_angle_format[stone_ind]:
            if (interval_start is None or interval_start <= angle) and (interval_end is None or angle <= interval_end):
                return True        
        return False
    
    @lru_cache(maxsize=2)
    def calculate_snap_point(self, x, y, color=None):
        candidate_points = []
        
        index_of_stone_that_containes_xy = index_of_stone_that_contains_a_point_or_none(x, y, self._stones, 2 * self._stone_radius)
        if index_of_stone_that_containes_xy is None and color is None:
            return x, y
        # if index_of_stone_that_containes_xy is not None:
        #     stone_that_containes_xy = self._stones[index_of_stone_that_containes_xy]
        #     center_x, center_y = stone_that_containes_xy.x, stone_that_containes_xy.y
        #     dist = math.sqrt(distance_squared(x - center_x, y - center_y))

        #     candidate_points.append((center_x + (x - center_x) / dist * 2 * self._stone_radius, center_y + (y - center_y) / dist * 2 * self._stone_radius))
        #     print("Here")
        
        for stone_ind, librety_intervals in enumerate(self._librety_intervals_in_xy_format):
            if color is not None and color != self._stones[stone_ind].color:
                continue
            
            center_x, center_y = self._stones[stone_ind].x, self._stones[stone_ind].y
            if self.has_liberty_in_direction(stone_ind, math.atan2(y - center_y, x - center_x)):
                # print(f"Stone {stone_ind} has librety at direction {math.atan2(y - center_y, x - center_x)}")
                dist = math.sqrt(distance_squared(x - center_x, y - center_y))
                candidate_points.append((center_x + (x - center_x) / dist * 2 * self._stone_radius, center_y + (y - center_y) / dist * 2 * self._stone_radius))
            # else:
                # print(f"Stone {stone_ind} does not have librety at direction {math.atan2(y - center_y, x - center_x)}")
            for xy_of_interval_start, xy_of_interval_end in librety_intervals:
                candidate_points.extend([xy_of_interval_start, xy_of_interval_end])
        
        if not candidate_points:
            return None, None

        index_of_closest_candidate = argmin(distance_squared(candidate_x - x, candidate_y - y) for candidate_x, candidate_y in candidate_points)
        # print(f"{x = }; {y = }")
        # print(f"temp = {[elem._asdict() for elem in self._stones]}")
        # print("gs = {\"stones\": temp[::]}")
        # print(f"polygons = {self._board_border_rectangles}")
        # print(f"candidate_points = {[(round(elem[0], 2), round(elem[1], 2)) for elem in candidate_points]}")
        # print(f"distances = {[distance_squared(candidate_x - x, candidate_y - y) for candidate_x, candidate_y in candidate_points]}")
        # print()
        return candidate_points[index_of_closest_candidate]
    
    def stone_has_librety(self, stone_ind):
        return bool(self._librety_intervals_in_angle_format[stone_ind])
    


class MyCache:
    def __init__(self, stone_radius, board):
        self.stone_radius = stone_radius
        self.board = board

        self._init_params_dict = dict()
        self.structures_dict = dict()
    
    def update(self, key, init_params):
        for key2, value in self._init_params_dict.items():
            if init_params == value:
                structure = self.structures_dict[key2]
                break
        else:
            structure = StoneStructure(*init_params.get("args", []), **init_params.get("kwargs", {}), stone_radius=self.stone_radius, board=self.board)

        self._init_params_dict[key] = copy.deepcopy(init_params)
        self.structures_dict[key] = structure
    
    def get_structure(self, key):
        return self.structures_dict[key]

