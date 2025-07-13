from collections import defaultdict
import shapely

from utils import has_uncovered_arc, reflect_point_over_line


class StoneStructure:
    def __init__(self, stones, stone_radius, board_inner):
        self._n = len(stones)
        self._stones = list(stones)
        self._stone_radius = stone_radius
        self._board_inner_coords = list(board_inner.boundary.coords)
        
        self._delone_neighbours = defaultdict(list)
        self._delone_edges_ind = []
        self._recalculate_delone_graph()
        self._calculate_who_had_dame()
    
    def _recalculate_delone_graph(self):
        points = shapely.MultiPoint([[stone.x, stone.y] for stone in self._stones])
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
    
    def calculate_connections_graph(self, tolerance=1e-5):
        return [[ind1, ind2] for ind1, ind2 in self._delone_edges_ind
                 if self._stones[ind1].distance_squared(self._stones[ind2]) <= 4 * self._stone_radius ** 2 + tolerance]
    
    def calculate_all_vertexes_within_distance(self, stone_ind, distance):
        rt_list = [stone_ind]
        rt_set = {stone_ind}
        ind = 0
        while ind < len(rt_list):
            cur_ind = rt_list[ind]
            for neigbour_ind in self._delone_neighbours[cur_ind]:
                if neigbour_ind not in rt_set and self._stones[stone_ind].distance_squared(self._stones[cur_ind]) <= distance:
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
    
    def _mirror_stone(self, x, y):
        rt = []
        for i in range(len(self._board_inner_coords) - 1):
            reflected_point_x, reflected_point_y = reflect_point_over_line(x, y, *self._board_inner_coords[i], *self._board_inner_coords[i + 1])
            rt.append((reflected_point_x, reflected_point_y, 2 * self._stone_radius))
        return rt
    
    def _calculate_who_had_dame(self):
        """assignes self._has_dame to the list[bool] where i-the element is true iff i-th stone has dame"""

        rt = [False] * self._n
        for ind in range(self._n):
            stone_circ = self._ind_to_circle(ind)
            stone_neighb = [self._ind_to_circle(neighb_ind) for neighb_ind in self.calculate_all_vertexes_within_distance(ind, 4 * self._stone_radius)]
            stone_neighb = stone_neighb[1:] # removing ind-th stone from his neighbours
            stone_circ_reflected = self._mirror_stone(stone_circ[0], stone_circ[1])
            rt[ind] = has_uncovered_arc(stone_circ, stone_neighb + stone_circ_reflected)
            #print(f"{ind = }\n{stone_circ = }\n{stone_neighb = }\n{stone_circ_reflected = }\n{rt[ind] = }\n")

        self._has_dame = rt
    
    def stone_has_dame(self, stone_ind):
        return self._has_dame[stone_ind]
