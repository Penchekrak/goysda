from types import SimpleNamespace
import numpy as np

colors = dict(
    white=(255, 255, 255),
    black=(0, 0, 0),
    red=(255, 0, 0),
    green=(0, 255, 0),
    blue=(0, 0, 255),
    light_grey=(211, 211, 211),
    dark_grey=(119, 119, 119),
)


default_config = {
    'width': 480,
    'height': 480,
    'fps': 60,
    'board_width': 300,
    'board_height': 300,
    'cloud_scale': 0.25,
    'background_color': 'green',
    'stone_radius': 10,
    'stone_color': 'white',
    'stone_no_click_zone_color': (50, 200, 200), # полупрозрачный серый
    'cloud_count': 10,
    'cloud_bulkiness': 10,
    'cloud_bulk_radius': 10,
    'stone_border_color': 'black',
    'stone_border_width': 2,
    'stone_border_radius': 10,
    'cloud_image_path': 'assets/cloud.jpg',
}

def norm(x, y):
    return x ** 2 + y ** 2

def stone_within_the_board(x, y, game_config):
    """
    Checks if the stone fits within the board.
    """
    r = game_config['stone_radius']
    w = game_config.width
    h = game_config.height
    return (x - r >= 0) and (x + r <= w) and (y - r >= 0) and (y + r <= h)


def stone_intersects_others(x0, y0, game_state, game_config):
    """
    Checks if stone does not intersect other stones.
    """
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

def compute_closest_snap_position(x, y, game_state, game_config, snap_color=None):
    dt_poitns = compute_double_touch_points(game_state, game_config, snap_color)
    pd_points = compute_perpendicular_touches(x, y, game_state, game_config, snap_color)
    possible_closest_points = dt_poitns + pd_points

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

    target_color = stones[stone_idx]["color"]
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
        if stone["color"] != target_color:
            continue

        group.append(idx)

        sx, sy = stone["x"], stone["y"]
        for j, other in enumerate(stones):
            if j in visited or other["color"] != target_color:
                continue
            dx = other["x"] - sx
            dy = other["y"] - sy
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
    for group in groups:
        if game_state.placed_stones[group[0]].color == color:
            if not group_has_dame(group, game_state, game_config):
                # TODO: add KO rule etc
                kill_group(group, game_state, game_config)

def group_has_dame(group, game_state, game_config):
    r = game_config['stone_radius']
    target_color = game_state.placed_stones[group[0]].color
    for s in group:
        x0, y0 = s.x, s.y
        x1, y1 = compute_closest_snap_position(x0, y0, game_state, game_config, snap_color=target_color)
        if norm(x1 - x0, y1 - y0) <= 4 * r ** 2 + 10**(-5):
            return True
    return False

def kill_group(group, game_state, game_config):
    game_state.placed_stones = [s for i, s in enumerate(game_state.placed_stones) if i not in group]