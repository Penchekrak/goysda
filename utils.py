from types import SimpleNamespace
import numpy as np
from functools import lru_cache
import pygame
import shapely


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

# board_size = 720
board_size = 600

world_size = 950

default_config = {
    'width': world_size,
    'height': world_size,
    'fps': 30,
    'board_width': board_size,
    'board_height': board_size,
    'cloud_scale': 0.25,
    'stone_radius': board_size / 26,
    'cloud_count': 10,
    'cloud_bulkiness': 10,
    'cloud_bulk_radius': 10,
    'cloud_image_path': 'assets/cloud.jpg',
    'stone_border_width': 2,
    'stone_border_radius': 10,
    'stone_no_click_zone_color': (50, 200, 200), # полупрозрачный серый
    'light_grey_territory_color': (191, 191, 191),
    'dark_grey_territory_color': (59, 59, 59),
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
    'board_border_color': (128, 128, 128),
    'board_color': (204, 102, 0),
    'board_blur_radius': 30,
    "border_alpha": 0.5,
    "default_alpha": 0.8,
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


def norm(x, y):
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

def stone_intersects_others(x0, y0, game_state, game_config):
    """
    Checks if stone does not intersect other stones.
    """
    if not stone_within_the_board(x0, y0, game_config):
        return True

    stones = game_state.placed_stones
    r = game_config['stone_radius']
    for stone in stones:
        x1, y1 = stone.x, stone.y
        if norm(x1 - x0, y1 - y0) < 4 * r ** 2 - 10**(-5):
            return True
    return False

def multiple_stones_intersect_others(new_stones_coords, game_state, game_config):
    """
    For each of the coords, checks if stone does not intersect other stones.
    NOTE: highly inefficient.
    TODO: rewrite this.
    """
    return [stone_intersects_others(*s, game_state, game_config) for s in new_stones_coords]

def compute_double_touch_points(game_state, game_config, snap_color=None):
    """
    Returns all possible placements where the point would touch two other stones simultaneously.
    """
    r = game_config['stone_radius']
    doubletouch_points = []
    for s1 in game_state.placed_stones:
        for s2 in game_state.placed_stones:

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

            if norm(vx, vy) > 16 * r ** 2:
                continue # no double touches
            elif norm(vx, vy) == 16 * r ** 2:
                doubletouch_points.append((
                    x1 + vx / 2, 
                    y1 + vy / 2
                ))
            else:
                # w is orthogonal to v
                wx, wy = vy, -vx
                
                # w is normed to 1
                w_norm = norm(wx, wy)
                wx /= np.sqrt(w_norm)
                wy /= np.sqrt(w_norm)

                # what do we need to add? sqrt(4r^2 - |v / 2|^2)
                add_norm = 4 * r ** 2 - norm(vx, vy) / 4
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

    is_ok = multiple_stones_intersect_others(doubletouch_points, game_state, game_config)

    return [s for (s, intersect) in zip(doubletouch_points, is_ok) if not intersect]
    
def compute_border_touch_points(game_state, game_config, snap_color=None):
    r = game_config['stone_radius']
    w = game_config['board_width']
    h = game_config['board_height']
    left = game_config['width'] / 2 - w / 2 + r
    right = game_config['width'] / 2 + w / 2 - r
    bottom = game_config['height'] / 2 - h / 2 + r
    top = game_config['height'] / 2 + h / 2 - r
    
    bordertouch_points = []

    for s in game_state.placed_stones:

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
    
    is_ok = multiple_stones_intersect_others(bordertouch_points, game_state, game_config)

    return [s for (s, intersect) in zip(bordertouch_points, is_ok) if not intersect]

def compute_perpendicular_touches(x0, y0, game_state, game_config, snap_color=None):

    x0 += np.random.randn() / 1000
    y0 += np.random.randn() / 1000

    r = game_config['stone_radius']
    perpendicular_points = []

    for s in game_state.placed_stones:
        x1, y1 = s.x, s.y

        if snap_color:
            if s.color != snap_color:
                continue

        # v is the s1 -> s2 vector
        vx = x1 - x0
        vy = y1 - y0
        # v is normed to 1
        v_norm = norm(vx, vy)
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

    is_ok = multiple_stones_intersect_others(perpendicular_points, game_state, game_config)

    return [s for (s, intersect) in zip(perpendicular_points, is_ok) if not intersect]

def compute_perpendicular_border_touches(x, y, game_state, game_config, snap_color=None):
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

    is_ok = multiple_stones_intersect_others(touches, game_state, game_config)

    return [s for (s, intersect) in zip(touches, is_ok) if not intersect]

def compute_closest_snap_position(x, y, game_state, game_config, snap_color=None, precomputed_doubletouch_points=None):
    if precomputed_doubletouch_points:
        dt_points = precomputed_doubletouch_points
    else:
        dt_points = compute_double_touch_points(game_state, game_config, snap_color)

    pd_points = compute_perpendicular_touches(x, y, game_state, game_config, snap_color)
    bt_points = compute_border_touch_points(game_state, game_config, snap_color)
    pbd_points = compute_perpendicular_border_touches(x, y, game_state, game_config, snap_color)
    possible_closest_points = dt_points + pd_points + bt_points + pbd_points

    min_d = np.inf
    xc = 0.0
    yc = 0.0

    for (x1, y1) in possible_closest_points:
        d = norm(x1 - x, y1 - y)
        if d < min_d:
            xc, yc = x1, y1
            min_d = d
        
    return xc, yc

def compute_group(stone_idx, game_state, game_config):
    r = game_config['stone_radius']
    stones = game_state.placed_stones

    target_color = stones[stone_idx].color
    threshold_sq = 4 * r ** 2

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
            if dx * dx + dy * dy <= threshold_sq + 10**(-5):
                stack.append(j)

    return group

def split_stones_by_groups(game_state, game_config):
    stones = game_state.placed_stones
    if not stones:
        return []

    groups = []
    visited = set()

    for idx in range(len(stones)):
        if idx in visited:
            continue
        group = compute_group(idx, game_state, game_config)
        visited.update(group)
        groups.append(group)

    return groups

def kill_groups_of_color(color, game_state, game_config):
    groups = split_stones_by_groups(game_state, game_config)
    stones_to_kill = []

    precomputed_doubletouch_points = compute_double_touch_points(game_state, game_config, None)

    for group in groups:
        if game_state.placed_stones[group[0]].color == color:
            if not group_has_dame(group, game_state, game_config, precomputed_doubletouch_points):
                # TODO: add KO rule etc
                stones_to_kill += group
    kill_group(stones_to_kill, game_state, game_config)

def group_has_dame(group, game_state, game_config, precomputed_doubletouch_points=None):
    r = game_config['stone_radius']
    
    if precomputed_doubletouch_points:
        dt_points = precomputed_doubletouch_points
    else:
        dt_points = compute_double_touch_points(game_state, game_config, None)
    for i in group:
        s = game_state.placed_stones[i]
        x0, y0 = s.x, s.y
        x1, y1 = compute_closest_snap_position(x0, y0, game_state, game_config, snap_color=None, precomputed_doubletouch_points=dt_points)
        if norm(x1 - x0, y1 - y0) <= 4 * r ** 2 + 10**(-5):
            return True
    return False

def kill_group(group, game_state, game_config):
    game_state.placed_stones = [s for i, s in enumerate(game_state.placed_stones) if i not in group]


def calculate_connections_graph(game_state, game_config, tolerance=1e-5):
    points = shapely.MultiPoint([[stone.x, stone.y] for stone in game_state.placed_and_suggestion_stones()])
    point_to_index = {point: i for i, point in enumerate(points.geoms)}
    delone_edges = shapely.delaunay_triangles(points, only_edges=True).geoms
    rt = []
    for edge in delone_edges:
        if edge.length <= 2 * game_config["stone_radius"] + tolerance:
            rt.append([point_to_index[elem] for elem in edge.boundary.geoms])
    return rt


def rotation_matrix(angle):
    return np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])


def calculate_two_connection_polygons(x1, y1, x2, y2):
    rt = []
    p1, p2 = np.array([x1, y1]), np.array([x2, y2])
    m = (p1 + p2) / 2
    for sign in [-1, 1]:
        a = p1
        b = p1 + (m - p1) @ rotation_matrix(sign * np.pi / 3)
        c = p1 + (2 * np.sqrt(3) / 3) * (m - p1) @ rotation_matrix(sign * np.pi / 6)
        d = m + (m - p1) @ rotation_matrix(sign * np.pi / 3)
        e = p2
        rt.append(shapely.Polygon([a, b, c, d, e]))
    return rt
        
        
