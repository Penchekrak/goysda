def snap_stone(user_input, snap_color=None, r=1.0):
    """
    If snap_to_color is False, then:
    * if stone can be placed at (x, y) we keep them
    * if the stone cannot be placed at (x, y), we move it to the nearest possible position to place it
    
    If snap_to_color is True, then we move the placement suggestion to the nearest possible space touching the stone of the snap_color color

    Arguments: 
    user_input: a tuple (x, y, snap_to_color)
    snap_color: color to force-snap to
    r: radius of the stones

    Returns:
    A tuple (x, y) - a position of the stone placement suggestion that should appear on the screen.
    """