import math

import pygame
import shapely

import utils


class Transformation:
    def __init__(self, offset_x, offset_y, boundary_polygon: shapely.Polygon, log_scale=0, log_scale_min=0, log_scale_max=2.5):
        self._offset_x = offset_x
        self._offset_y = offset_y
        self._boundary_polygon = boundary_polygon
        self._log_scale = log_scale
        self._log_scale_min = log_scale_min
        self._log_scale_max = log_scale_max

        self._init_pararms = {"offset_x": offset_x, "offset_y": offset_y, "log_scale": log_scale, "log_scale_min": log_scale_min, "log_scale_max": log_scale_max, "boundary_polygon": boundary_polygon}
    
    def reset(self):
        self.__init__(**self._init_pararms)

    def scale(self):
        return math.exp(self._log_scale)

    def world_to_screen(self, wx, wy):
        x = int(wx * self.scale() + self._offset_x)
        y = int(wy * self.scale() + self._offset_y)
        return x, y

    def world_to_screen_distance(self, wd):
        return wd * self.scale()

    def screen_to_world(self, sx, sy):
        x = (sx - self._offset_x) / self.scale()
        y = (sy - self._offset_y) / self.scale()
        return (x, y)

    def _project_onto_allowed_configurations_set(self):
        # self._log_scale = min(self._log_scale, self._log_scale_max)
        self._log_scale = max(self._log_scale, self._log_scale_min)

        scale = 1 - self.scale()
        allowed_offset_polygon = shapely.affinity.affine_transform(self._boundary_polygon, (scale, 0, 0, scale, 0, 0))
        self._offset_x, self._offset_y = utils.project_point_onto_polygon(allowed_offset_polygon, shapely.Point(self._offset_x, self._offset_y)).coords[0]
   
    def compose_inplace(self, other):
        self._offset_x += self.scale() * other._offset_x
        self._offset_y += self.scale() * other._offset_y 
        self._log_scale += other._log_scale

    def update_self_zoom(self, mouse_wx, mouse_wy, log_zoom_delta):
        if self._log_scale + log_zoom_delta >= self._log_scale_max:
            return
        if self._log_scale + log_zoom_delta <= self._log_scale_min:
            return
        coeff = (1 - math.exp(log_zoom_delta))

        self.compose_inplace(Transformation(mouse_wx * coeff, mouse_wy * coeff, self._boundary_polygon, log_scale=log_zoom_delta))
        self._project_onto_allowed_configurations_set()
        
    def update_self_drag(self, delta_wx, delta_wy):
        delta_sx, delta_sy = self.world_to_screen(delta_wx, delta_wy)
        self._offset_x += delta_sx 
        self._offset_y += delta_sy 
        self._project_onto_allowed_configurations_set()
    
    def calculate_new_scale_and_offset(self, surface_to_transform_and_blit):
        stt_size = surface_to_transform_and_blit.get_size()
        stt_size_after_scaling = (stt_size[0] * self.scale(), stt_size[1] * self.scale())

        # Blit the source surface at the computed offset
        return stt_size_after_scaling, (self._offset_x, self._offset_y)

    def __str__(self):
        return f"{self.__class__.__name__}(offset_x={round(self._offset_x, 2)}, offset_y={round(self._offset_y, 2)}, scale={self.scale()})"    
    
    __repr__ = __str__
