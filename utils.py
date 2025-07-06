from types import SimpleNamespace

colors = dict(
    white=(255, 255, 255),
    black=(0, 0, 0),
    red=(255, 0, 0),
    green=(0, 255, 0),
    blue=(0, 0, 255),
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
    'stone_border_color': 'black',
    'stone_border_width': 2,
    'stone_border_radius': 10,
    'stone_border_radius': 10,
    'cloud_image_path': 'assets/cloud.jpg',
}


def stone_within_the_board(x, y, game_config):
    r = game_config.stone_radius
    w = game_config.width
    h = game_config.height
    return (x - r >= 0) and (x + r <= w) and (y - r >= 0) and (y + r <= h)


def stone_intersects_others(x0, y0, game_state, game_config):
    stones = game_state.stones
    r = game_config.stone_radius
    for stone in stones:
        x1, y1 = stone.x, stone.y
        if (x1 - x0) ** 2 + (y1 - y0) ** 2 < r:
            return True
    return False