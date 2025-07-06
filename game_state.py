from typing import Literal, NamedTuple, Tuple
from handle_input import ActionType
from utils import default_config
from snapper import snap_stone

from dataclasses import dataclass
import pygame

def snapping_mock(stone, list_of_stones):
    return stone

class Stone(NamedTuple):
    x: int
    y: int
    color: Literal['white', 'black']

@dataclass
class Cloud:
    x: int
    y: int
    velocity_x: int
    velocity_y: int



class GameState:
    def __init__(self, config):
        self.placed_stones = []
        self.player_to_move = 0
        self.config = config
        self.cloud_state = [Cloud(x=0, y=0)]

    def update_clouds(self):
        cloud_surface = pygame.image.load(self.config['cloud_image_path']).convert()
        cloud_height = cloud_surface.get_height()
        cloud_width = cloud_surface.get_width()


        for cloud in self.cloud_state:
            cloud.x += cloud.velocity_x
            cloud.y += cloud.velocity_y
            
            if cloud.x + self.config['cloud_scale'] * cloud_width > self.config['width']:
                cloud.velocity_x = -cloud.velocity_x
            if cloud.y + self.config['cloud_scale'] * cloud_height > self.config['height']:
                cloud.velocity_y = -cloud.velocity_y
            if cloud.x < 0:
                cloud.velocity_x = -cloud.velocity_x
            if cloud.y < 0:
                cloud.velocity_y = -cloud.velocity_y

        for i, cloud_0 in enumerate(self.cloud_state):
            for j in range(i):

                cloud_1 = self.cloud_state[j]
                
                if abs(cloud_0.x - cloud_1.x) < self.config['cloud_scale'] * cloud_width and abs(cloud_0.y - cloud_1.y) < self.config['cloud_scale'] * cloud_height:
                    cloud_0.velocity_x = -cloud_0.velocity_x
                    cloud_1.velocity_x = -cloud_1.velocity_x
                
                # if cloud_1.x - cloud_0.x > - self.config['cloud_scale'] * cloud_width:
                #     print("collision")
                #     cloud_0.velocity_x = -cloud_0.velocity_x
                #     cloud_1.velocity_x = -cloud_1.velocity_x
                # if cloud_1.y + self.config['cloud_scale'] * cloud_height > cloud_0.y:
                #     print("collision")
                #     cloud_0.velocity_y = -cloud_0.velocity_y
                #     cloud_1.velocity_y = -cloud_1.velocity_y
           
    

    def update(self, user_input):
        self.update_clouds()