from utils import *

def snap_stone(user_input, game_state, game_config, snap_color=None):
    """
    If snap_to_color is False, then:
    * if stone can be placed at (x, y) we keep them
    * if the stone cannot be placed at (x, y), we move it to the nearest possible position to place it
    
    If snap_to_color is True, then we move the placement suggestion to the nearest possible space touching the stone of the snap_color color

    Arguments: 
    user_input: a tuple (x, y, snap_to_color)
    game_state: state of the game: (existing stone placements etc)
    game_config: configuration of the game (probably thing like board shape etc)
    snap_color: color to force-snap to

    Returns:
    A tuple (x, y) - a position of the stone placement suggestion that should appear on the screen.
    """

    x, y, snap_to_color = user_input

    # TODO: if not within the board, problems. Fix this.
    if not stone_intersects_others(x, y, game_state, game_config):
        return x, y
    else:
        dt_poitns = compute_double_touch_points(game_state, game_config)
        pd_points = compute_perpendicular_touches(x, y, game_state, game_config)
        possible_closest_points = dt_poitns + pd_points

        min_d = np.inf
        xc = 0.0
        yc = 0.0

        for (x1, y1) in possible_closest_points:
            d = norm(x1 - x, y1 - y)
            if d < min_d:
                xc, yc = x1, y1
                d = min_d
            
        return xc, yc