import math
from functools import lru_cache

import numpy as np
import pygame
import shapely
import shapely.ops


colors = dict(
    white=(255, 255, 255),
    black=(0, 0, 0),
    red=(255, 0, 0),
    green=(0, 255, 0),
    blue=(0, 0, 255),
    light_blue=(193, 226, 230),  
    dark_blue=(85, 85, 139),       
    light_grey=(151, 151, 151),
    dark_grey=(69, 69, 69),
)

board_size = r = 720
# board_size = 600

world_size = 950

default_config = {
    'width': world_size,
    'height': world_size,
    'fps': 30,
    'board_width': board_size,
    'board_height': board_size,
    'board_polygon':  [[0, 0], [board_size, 0], [board_size, board_size], [0, board_size]], 
    #'board_polygon':  [[100, 0], [board_size, 0], [board_size, board_size], [0, board_size], [0, 100], [100, 100]],
    # 'board_polygon':  [[0, r / 2], [r/4, r * (1 - math.sqrt(3) / 2) / 2], [3 * r/4, r * (1 - math.sqrt(3) / 2) / 2], [r, r / 2], [3 * r / 4 , r * (1 + math.sqrt(3) / 2) / 2], [r / 4 , r * (1 + math.sqrt(3) / 2) / 2]], 
    'board_color': (204, 102, 0),
    'cloud_scale': 0.25,
    'stone_radius': board_size / 19 / 2,
    'cloud_count': 10,
    'cloud_bulkiness': 10,
    'cloud_bulk_radius': 10,
    'cloud_image_path': 'assets/cloud.jpg',
    'stone_border_width': 2,
    'stone_border_radius': 10,
    'white_territory_color': (191, 191, 191),
    'white_suggestion_territory_color': (181, 181, 181),
    'white_small_librety_color': (219,112,147),
    'white_suggestion_small_librety_color': (195, 117, 141),
    'black_territory_color': (59, 59, 59),
    'black_suggestion_territory_color': (69, 69, 69),
    'white_connection_color': (235, 235, 235),
    'white_border_color': (201, 201, 201),
    'white_connection_suggestion_color': (215, 215, 215),
    'white_suggestion_color': (201, 201, 201),
    'white_suggestion_border_color': (151, 151, 151),
    'black_connection_color': (20, 20, 20),
    'black_border_color': (50, 50, 50),
    'black_connection_suggestion_color': (30, 30, 30),
    'black_suggestion_color': (40, 40, 40),
    'black_suggestion_border_color': (69, 69, 69),
    'black_small_librety_color': (139, 0, 0),
    'black_suggestion_small_librety_color': (135, 40, 40),
    'board_border_color': (128, 128, 128),
    'board_blur_radius': 30,
    "border_alpha": 0.5,
    "default_alpha": 0.8,
    'zoom_speed': 0.1,
    "line_width": 1.5,
    "window title": 'Sugo - continious Go',
    'minimal_librety_angle_to_hightlight': math.pi / 180 * 20,
    "komi": 6.5,
}

def update_colors(config):
    suffix_color = "_color"
    suffix_alpha = "_alpha"
    alphas_config = {key[:-len(suffix_alpha)]: value for key, value in config.items() if key.endswith(suffix_alpha)}
    for key, value in config.items():
        if key.endswith(suffix_color):
            key_minus_suffix = key[:-len(suffix_color)]
            for key_alpha, value_alpha in alphas_config.items():
                if key_alpha in key:
                    alpha = value_alpha
                    break
            else:
                alpha = config["default_alpha"]
            colors[key_minus_suffix] = tuple(alpha * elem1 + (1 -  alpha) * elem2 for elem1, elem2 in zip(config[key], config["board_color"]))


def calculate_deltax_deltay(config):
    return (config['width'] - config['board_width']) / 2, (config['height'] - config['board_height']) / 2


def distance_squared(x, y):
    return x ** 2 + y ** 2

def stone_within_the_board(x, y, game_config):
    """
    Checks if the stone fits within the board.
    """
    r = game_config['stone_radius']
    w = game_config['board_width']
    h = game_config['board_height']
    left = game_config['width'] / 2 - w / 2
    right = game_config['width'] / 2 + w / 2
    bottom = game_config['height'] / 2 - h / 2
    top = game_config['height'] / 2 + h / 2
    return (x - r >= left) and (x + r <= right) and (y - r >= bottom) and (y + r <= top)

def stone_intersects_others(x0, y0, stones_list, game_config):
    """
    Checks if stone does not intersect other stones.
    """
    if not stone_within_the_board(x0, y0, game_config):
        return True

    r = game_config['stone_radius']
    for stone in stones_list:
        x1, y1 = stone.x, stone.y
        if distance_squared(x1 - x0, y1 - y0) < 4 * r ** 2 - 10**(-5):
            return True
    return False

def multiple_stones_intersect_others(new_stones_coords, stones_list, game_config):
    """
    For each of the coords, checks if stone does not intersect other stones.
    NOTE: highly inefficient.
    TODO: rewrite this.
    """
    return [stone_intersects_others(*s, stones_list, game_config) for s in new_stones_coords]

def compute_double_touch_points(stones_list, game_config, snap_color=None):
    """
    Returns all possible placements where the point would touch two other stones simultaneously.
    """
    r = game_config['stone_radius']
    doubletouch_points = []
    for s1 in stones_list:
        for s2 in stones_list:

            if snap_color:
                if s1.color != snap_color and s2.color != snap_color:
                    continue

            x1, y1 = s1.x, s1.y
            x2, y2 = s2.x, s2.y

            if x1 == x2 and y1 == y2:
                continue

            # v is the s1 -> s2 vector
            vx = x2 - x1
            vy = y2 - y1

            if distance_squared(vx, vy) > 16 * r ** 2:
                continue # no double touches
            elif distance_squared(vx, vy) == 16 * r ** 2:
                doubletouch_points.append((
                    x1 + vx / 2, 
                    y1 + vy / 2
                ))
            else:
                # w is orthogonal to v
                wx, wy = vy, -vx
                
                # w is normed to 1
                w_norm = distance_squared(wx, wy)
                wx /= np.sqrt(w_norm)
                wy /= np.sqrt(w_norm)

                # what do we need to add? sqrt(4r^2 - |v / 2|^2)
                add_norm = 4 * r ** 2 - distance_squared(vx, vy) / 4
                wx *= np.sqrt(add_norm)
                wy *= np.sqrt(add_norm)

                doubletouch_points.append((
                    x1 + vx / 2 + wx,
                    y1 + vy / 2 + wy,
                ))
                doubletouch_points.append((
                    x1 + vx / 2 - wx,
                    y1 + vy / 2 - wy,
                ))

    is_ok = multiple_stones_intersect_others(doubletouch_points, stones_list, game_config)

    return [s for (s, intersect) in zip(doubletouch_points, is_ok) if not intersect]
    
def compute_border_touch_points(stones_list, game_config, snap_color=None):
    r = game_config['stone_radius']
    w = game_config['board_width']
    h = game_config['board_height']
    left = game_config['width'] / 2 - w / 2 + r
    right = game_config['width'] / 2 + w / 2 - r
    bottom = game_config['height'] / 2 - h / 2 + r
    top = game_config['height'] / 2 + h / 2 - r
    
    bordertouch_points = []

    for s in stones_list:

        if s.color != snap_color:
            continue

        x, y = s.x, s.y

        if x - left <= 2 * r:
            add = 4 * r ** 2 - (x - left) ** 2
            bordertouch_points.append((left, y + np.sqrt(add)))
            bordertouch_points.append((left, y - np.sqrt(add)))
        if right - x <= 2 * r:
            add = 4 * r ** 2 - (right - x) ** 2
            bordertouch_points.append((right, y + np.sqrt(add)))
            bordertouch_points.append((right, y - np.sqrt(add)))
        if y - bottom <= 2 * r:
            add = 4 * r ** 2 - (y - bottom) ** 2
            bordertouch_points.append((x + np.sqrt(add), bottom))
            bordertouch_points.append((x - np.sqrt(add), bottom))
        if top - y <= 2 * r:
            add = 4 * r ** 2 - (top - y) ** 2
            bordertouch_points.append((x + np.sqrt(add), top))
            bordertouch_points.append((x - np.sqrt(add), top))
    
    is_ok = multiple_stones_intersect_others(bordertouch_points, stones_list, game_config)

    return [s for (s, intersect) in zip(bordertouch_points, is_ok) if not intersect]

def compute_perpendicular_touches(x0, y0, stones_list, game_config, snap_color=None):

    x0 += np.random.randn() / 1000
    y0 += np.random.randn() / 1000

    r = game_config['stone_radius']
    perpendicular_points = []

    for s in stones_list:
        x1, y1 = s.x, s.y

        if snap_color:
            if s.color != snap_color:
                continue

        # v is the s1 -> s2 vector
        vx = x1 - x0
        vy = y1 - y0
        # v is normed to 1
        v_norm = distance_squared(vx, vy)
        vx /= np.sqrt(v_norm)
        vy /= np.sqrt(v_norm)
        
        perpendicular_points.append((
            x1 + vx * 2 * r,
            y1 + vy * 2 * r
        ))
        perpendicular_points.append((
            x1 - vx * 2 * r,
            y1 - vy * 2 * r
        ))

    is_ok = multiple_stones_intersect_others(perpendicular_points, stones_list, game_config)

    return [s for (s, intersect) in zip(perpendicular_points, is_ok) if not intersect]

def compute_perpendicular_border_touches(x, y, stones_list, game_config, snap_color=None):
    r = game_config['stone_radius']
    w = game_config['board_width']
    h = game_config['board_height']
    left = game_config['width'] / 2 - w / 2 + r
    right = game_config['width'] / 2 + w / 2 - r
    bottom = game_config['height'] / 2 - h / 2 + r
    top = game_config['height'] / 2 + h / 2 - r
    
    if snap_color:
        return []

    touches = [
        (x, top),
        (x, bottom),
        (left, y),
        (right, y),
        (left, top),
        (left, bottom),
        (right, top),
        (right, bottom)
    ]

    is_ok = multiple_stones_intersect_others(touches, stones_list, game_config)

    return [s for (s, intersect) in zip(touches, is_ok) if not intersect]

def compute_closest_snap_position(x, y, stones_list, game_config, snap_color=None, precomputed_doubletouch_points=None):
    if precomputed_doubletouch_points:
        dt_points = precomputed_doubletouch_points
    else:
        dt_points = compute_double_touch_points(stones_list, game_config, snap_color)

    pd_points = compute_perpendicular_touches(x, y, stones_list, game_config, snap_color)
    bt_points = compute_border_touch_points(stones_list, game_config, snap_color)
    pbd_points = compute_perpendicular_border_touches(x, y, stones_list, game_config, snap_color)
    possible_closest_points = dt_points + pd_points + bt_points + pbd_points

    min_d = np.inf
    xc = 0.0
    yc = 0.0

    for (x1, y1) in possible_closest_points:
        d = distance_squared(x1 - x, y1 - y)
        if d < min_d:
            xc, yc = x1, y1
            min_d = d
        
    return xc, yc

def compute_group(stone_idx, stones_list, game_config):
    r = game_config['stone_radius']
    stones = stones_list

    target_color = stones[stone_idx].color
    threshold_sq = (2 * r + 1e-5) ** 2 

    visited = set()
    stack = [stone_idx]
    group = []

    while stack:
        idx = stack.pop()
        if idx in visited:
            continue
        visited.add(idx)

        stone = stones[idx]
        if stone.color != target_color:
            continue

        group.append(idx)

        sx, sy = stone.x, stone.y
        for j, other in enumerate(stones):
            if j in visited or other.color != target_color:
                continue
            dx = other.x - sx
            dy = other.y - sy
            if dx * dx + dy * dy <= threshold_sq:
                stack.append(j)

    return group

def split_stones_by_groups(stones_list, game_config):
    stones = stones_list
    if not stones:
        return []

    groups = []
    visited = set()

    for idx in range(len(stones)):
        if idx in visited:
            continue
        group = compute_group(idx, stones_list, game_config)
        visited.update(group)
        groups.append(group)

    return groups

def group_has_librety(group, stones_structure):
    return any(stones_structure.stone_has_librety(i) for i in group)


def rotation_matrix(angle):
    return np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])


def calculate_connection_polygon(x1, y1, x2, y2):
    rt = []
    p1, p2 = np.array([x1, y1]), np.array([x2, y2])
    m = (p1 + p2) / 2
    return shapely.Polygon([
        p1 + (m - p1) @ rotation_matrix(np.pi / 3),
        p1 + (2 * np.sqrt(3) / 3) * (m - p1) @ rotation_matrix(np.pi / 6),
        m + (m - p1) @ rotation_matrix(np.pi / 3),
        m + (m - p1) @ rotation_matrix(-np.pi / 3),
        p1 + (2 * np.sqrt(3) / 3) * (m - p1) @ rotation_matrix(-np.pi / 6),
        p1 + (m - p1) @ rotation_matrix(-np.pi / 3),
    ])
        
        
def get_opposite_color(color, list_of_two_colors):
    if list_of_two_colors[0] in color:
        return color.replace(list_of_two_colors[0], list_of_two_colors[1])
    if list_of_two_colors[1] in color:
        return color.replace(list_of_two_colors[1], list_of_two_colors[0])
    
    raise ValueError(f"Bad color to find opposite color to: {color}")


def get_cross_polygon(center_x, center_y, cross_height, cross_width):
    x, y, h, w = center_x, center_y, cross_height, cross_width
    return shapely.Polygon([
        [x - w, y],
        [x - w - h, y + h],
        [x - h, y + w + h],
        [x, y + w],
        [x + h, y + w + h],
        [x + w + h, y + h],
        [x + w, y],
        [x + w + h, y - h],
        [x + h, y - w - h],
        [x, y - w],
        [x - h, y - w - h],
        [x - w - h, y - h],
    ])


def project_point_onto_polygon(polygon, point):
    """
    Finds the closes point to 'point' inside the 'polygon' or in the boundary.

    Args:
        polygon: A shapely Polygon object.
        point: A shapely Point object.

    Returns:
        A shapely Point object representing the projection
    """
    if polygon.contains(point):
        return point
            
    return shapely.ops.nearest_points(point, polygon.exterior)[1]


def is_control_pressed():
    return pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]


def argmin(iterator):
    iterator = iter(iterator)
    argmin = 0
    valmin = next(iterator)
    for ind, val in enumerate(iterator):
        if val < valmin:
            argmin = ind + 1
            valmin = val

    return argmin


def remove_interior_if_it_exists(polygon):
    if len(polygon.interiors) > 2:
        raise NotImplementedError
    
    if not polygon.interiors:
        return polygon

    exterior = list(polygon.exterior.coords)
    interior = list(polygon.interiors[0].coords)[::-1]
    closest_interior_point_index = argmin(distance_squared(elem[0] - exterior[0][0], elem[1] - exterior[0][1]) for elem in interior)

    interior = interior[closest_interior_point_index:] + interior[:closest_interior_point_index]
    new_ring = []
    new_ring.extend(exterior)
    new_ring.extend(interior)
    new_ring.append(interior[0])
    return shapely.Polygon(new_ring)


def index_of_stone_that_contains_a_point_or_none(point_x, point_y, stones_list, stones_radius):
    for stone_idx, stone in enumerate(stones_list):
        if distance_squared(stone.x - point_x, stone.y - point_y) <= stones_radius ** 2:
            return stone_idx
    
    return None


def point_in_polygon(x, y, poly):
    n = len(poly)
    inside = False
    for i in range(n):
        j = (i - 1) % n
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
    return inside

def circle_line_segment_intersection(x0, y0, r0, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    A = dx * dx + dy * dy
    B = 2 * (dx * (x1 - x0) + dy * (y1 - y0))
    C = (x1 - x0) ** 2 + (y1 - y0) ** 2 - r0 ** 2
    discriminant = B * B - 4 * A * C
    if discriminant < 0:
        return []
    sqrt_disc = math.sqrt(discriminant)
    t1 = (-B - sqrt_disc) / (2 * A)
    t2 = (-B + sqrt_disc) / (2 * A)
    intersections = []
    for t in [t1, t2]:
        if 0 <= t <= 1:
            x = x1 + t * dx
            y = y1 + t * dy
            angle = math.atan2(y - y0, x - x0)
            intersections.append(angle)
    return intersections

def find_uncovered_arcs(circle_C, list_of_circles, list_of_polygons, alpha, epsilon=1e-5):
    left_end, right_end = -math.pi, math.pi

    x0, y0, r0 = circle_C
    two_pi = 2 * math.pi
    
    intervals = []
    
    for circle in list_of_circles:
        x, y, r_d = circle
        dx = x - x0
        dy = y - y0
        d_sq = dx*dx + dy*dy
        d = math.sqrt(d_sq)
        
        if d >= r0 + r_d:
            continue
            
        if d <= abs(r0 - r_d):
            if r_d >= r0:
                intervals.append((-math.pi, math.pi))
            continue

        cos_theta = (r0*r0 + d_sq - r_d*r_d) / (2 * r0 * d)
        if cos_theta < -1:
            cos_theta = -1
        elif cos_theta > 1:
            cos_theta = 1
        theta = math.acos(cos_theta)
        phi = math.atan2(dy, dx)
        
        a = phi - theta
        b = phi + theta

        if a <= b:
            intervals.extend([(a - two_pi, b - two_pi), (a, b), (a + two_pi, b + two_pi)])
        elif a < math.pi:
            intervals.extend([(-two_pi + a, b), (a, two_pi + b)])
    
    for polygon in list_of_polygons: # for polygon in list_of    for polygon in list_of_polygons: # if polygons has obtuse angle this function may return incorrest answer
        intersections = []
        any_intersection = False
        n_vertices = len(polygon)
        for i in range(n_vertices):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % n_vertices]
            segment_intersections = circle_line_segment_intersection(x0, y0, r0, x1, y1, x2, y2)
            intersections.extend(segment_intersections)
        # print(intersections)
        
        n_intersect = len(intersections)
        intersections = sorted(intersections)
        for i in range(n_intersect):
            start_angle = intersections[i]
            end_angle = intersections[(i + 1) % n_intersect]
            if end_angle < start_angle:
                end_angle += two_pi
            
            mid_angle = (start_angle + end_angle) / 2.0
            mid_x = x0 + r0 * math.cos(mid_angle)
            mid_y = y0 + r0 * math.sin(mid_angle)
            if point_in_polygon(mid_x, mid_y, polygon):
                # print(f"{start_angle = }, {end_angle = }")
                if end_angle > math.pi:
                    intervals.append((start_angle, end_angle))
                    intervals.append((start_angle - two_pi, end_angle - two_pi))
                else:
                    intervals.append((start_angle, end_angle))
    if not intervals:
        return [(left_end, right_end)]
    
    intervals.sort()
    merged = []
    current_start, current_end = intervals[0]
    for i in range(1, len(intervals)):
        s, e = intervals[i]
        if s + 1e-5 < current_end:
            current_end = max(current_end, e)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = s, e
    merged.append((current_start, current_end))
    
    merged = [[s, e] for s, e in merged if e >= -math.pi and s <= math.pi]
    merged = [[s, e] for s, e in merged if e > s + 1e-5]
    if not merged:
        return [(left_end, right_end)]
    
    gaps = []
    if -math.pi <= merged[0][0]:
        gaps.append((merged[-1][1] - two_pi, merged[0][0]))
    gaps.extend([(merged[i][1], merged[i + 1][0]) for i in range(len(merged) - 1)])
    if merged[-1][1] < math.pi:
        gaps.append((merged[-1][1], merged[0][0] + two_pi))

    # print(f"{intervals = }\n{merged = }\n{gaps = }\n")
    return gaps


def thicken_a_line_segment(x0, y0, x1, y1, width):
    perp_dir = -(y1 - y0), (x1 - x0)
    c = 1 / math.sqrt(distance_squared(*perp_dir)) * width
    perp_dir = [perp_dir[0] * c, perp_dir[1] * c] 
    return [
        [x0 + perp_dir[0], y0 + perp_dir[1]],
        [x1 + perp_dir[0], y1 + perp_dir[1]],
        [x1 - perp_dir[0], y1 - perp_dir[1]],
        [x0 - perp_dir[0], y0 - perp_dir[1]],
    ]
