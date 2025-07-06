from utils import stone_within_the_board, stone_intersects_others

def snap_stone(user_input, game_config, game_state, snap_color=None):
    """
    If snap_to_color is False, then:
    * if stone can be placed at (x, y) we keep them
    * if the stone cannot be placed at (x, y), we move it to the nearest possible position to place it
    
    If snap_to_color is True, then we move the placement suggestion to the nearest possible space touching the stone of the snap_color color

    Arguments: 
    user_input: a tuple (x, y, snap_to_color)
    game_config: configuration of the game (probably thing like board shape etc)
    game_state: state of the game: (existing stone placements etc)
    snap_color: color to force-snap to

    Returns:
    A tuple (x, y) - a position of the stone placement suggestion that should appear on the screen.
    """

    x, y, snap_to_color = user_input
    r = game_config.stone_radius

    if not snap_to_color:
        if stone_within_the_board(x,y, game_config) and not stone_intersects_others(x, y, game_state):
            return x, y


    return x, y