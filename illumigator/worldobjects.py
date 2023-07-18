from abc import abstractmethod
import arcade
import numpy
import math
import time

from illumigator import light
from illumigator import util
from illumigator import geometry
from illumigator import object_animation


class WorldObject:

    def __init__(
        self,
        position: numpy.ndarray,
        rotation_angle: float, *,
        is_interactable=False,
    ):
        self._position: numpy.ndarray = position
        self._rotation_angle: float = rotation_angle
        self._is_interactable: bool = is_interactable
        self._geometry_segments: list[geometry.Geometry] = []
        self.obj_animation: object_animation.ObjectAnimation | None = None

        self._sprite_list: arcade.SpriteList = arcade.SpriteList()

    def initialize_sprites(self, sprite_info: tuple, dimensions: numpy.ndarray | None = None):
        sprite_path, sprite_scale, sprite_width, sprite_height = sprite_info
        if dimensions is None:
            self._sprite_list.append(
                util.load_sprite(
                    sprite_path,
                    sprite_scale,
                    image_width=sprite_width,
                    image_height=sprite_height,
                    center_x=self._position[0],
                    center_y=self._position[1],
                    angle=numpy.rad2deg(self._rotation_angle),
                    hit_box_algorithm="Simple",
                )
            )

        else:
            axis1_norm = numpy.array([math.cos(self._rotation_angle), math.sin(self._rotation_angle)])
            axis2_norm = numpy.array([-math.sin(self._rotation_angle), math.cos(self._rotation_angle)])
            axis1 = 0.5 * sprite_width * sprite_scale * dimensions[0] * axis1_norm
            axis2 = 0.5 * sprite_height * sprite_scale * dimensions[1] * axis2_norm

            for col in range(int(dimensions[0])):
                for row in range(int(dimensions[1])):
                    sprite_center = (self._position - axis1 - axis2) + sprite_scale * (
                            (sprite_width * (col + 0.5) * axis1_norm)
                            + (sprite_height * (row + 0.5) * axis2_norm)
                    )

                    self._sprite_list.append(
                        util.load_sprite(
                            sprite_path,
                            sprite_scale,
                            image_width=sprite_width,
                            image_height=sprite_height,
                            center_x=sprite_center[0],
                            center_y=sprite_center[1],
                            angle=numpy.rad2deg(self._rotation_angle),
                            hit_box_algorithm="Simple",
                        )
                    )

    def initialize_geometry(self, sprite_info: tuple, dimensions: numpy.ndarray = numpy.ones(2), *, all_borders: bool = False):
        sprite_path, sprite_scale, sprite_width, sprite_height = sprite_info
        axis1_norm = numpy.array([math.cos(self._rotation_angle), math.sin(self._rotation_angle)])
        axis2_norm = numpy.array([-math.sin(self._rotation_angle), math.cos(self._rotation_angle)])
        axis1 = 0.5 * sprite_width * sprite_scale * dimensions[0] * axis1_norm
        axis2 = 0.5 * sprite_height * sprite_scale * dimensions[1] * axis2_norm
        if all_borders is True:
            self._geometry_segments = [
                geometry.Line(self, self._position - axis1 - axis2, self._position - axis1 + axis2),
                geometry.Line(self, self._position - axis1 + axis2, self._position + axis1 + axis2),
                geometry.Line(self, self._position + axis1 + axis2, self._position + axis1 - axis2),
                geometry.Line(self, self._position + axis1 - axis2, self._position - axis1 - axis2),
            ]
        else:  # Only do the diagonals
            self._geometry_segments = [
                geometry.Line(self, self._position - axis1 - axis2, self._position + axis1 + axis2),
                geometry.Line(self, self._position - axis1 + axis2, self._position + axis1 - axis2),
            ]


    def draw(self):
        self._sprite_list.draw(pixelated=True)
        if util.DEBUG_GEOMETRY:
            for segment in self._geometry_segments:
                segment.draw()

    def distance_squared_to_center(self, point_x, point_y):
        return util.distance_squared(self._position, numpy.array([point_x, point_y]))

    def check_collision(self, sprite: arcade.Sprite):
        return sprite.collides_with_list(self._sprite_list)

    def move_geometry(self, move_distance: numpy.ndarray = numpy.zeros(2), rotate_angle: float = 0):
        for segment in self._geometry_segments:
            segment.move(self._position, move_distance, rotate_angle=rotate_angle)
        self._position = self._position + move_distance
        self._rotation_angle = self._rotation_angle + rotate_angle

    def move_if_safe(
        self,
        character,
        move_distance: numpy.ndarray = numpy.zeros(2),
        rotate_angle: float = 0,
    ) -> bool:
        for sprite in self._sprite_list:
            new_position = (
                util.rotate_around_center(
                    self._position,
                    numpy.array([sprite.center_x, sprite.center_y]),
                    rotate_angle,
                )
                + move_distance
            )
            sprite.radians += rotate_angle
            sprite.center_x, sprite.center_y = new_position[0], new_position[1]
        if self.check_collision(character.character_sprite):
            for sprite in self._sprite_list:
                new_position = util.rotate_around_center(
                    self._position,
                    numpy.array([sprite.center_x, sprite.center_y]) - move_distance,
                    -rotate_angle,
                )
                sprite.radians -= rotate_angle
                sprite.center_x, sprite.center_y = new_position[0], new_position[1]
            return False
        self.move_geometry(move_distance, rotate_angle)
        return True

    def create_animation(self, travel: numpy.ndarray, dt: float = 0.01, angle_travel: float = 0):
        self.obj_animation = object_animation.ObjectAnimation(
            self._position,
            self._position + travel,
            dt,
            angle1=self._rotation_angle,
            angle2=self._rotation_angle + angle_travel,
        )

    def apply_object_animation(self, character):
        # Test for sprite collisions
        animation_data = self.obj_animation.get_new_position()
        position_change = animation_data[0] - self._position
        angle_change = animation_data[1] - self._rotation_angle
        if not self.move_if_safe(
            character, move_distance=position_change, rotate_angle=angle_change
        ):  # If move is unsafe
            self.obj_animation.backtrack()


class Wall(WorldObject):
    def __init__(self, position: numpy.ndarray, dimensions: numpy.ndarray, rotation_angle: float):
        super().__init__(position, rotation_angle, is_interactable=False)
        self.initialize_geometry(util.WALL_SPRITE_INFO, dimensions, all_borders=False)
        self.initialize_sprites(util.WALL_SPRITE_INFO, dimensions)


class Mirror(WorldObject):
    def __init__(self, position: numpy.ndarray, rotation_angle: float):
        super().__init__(position, rotation_angle, is_interactable=True)
        self.initialize_geometry(util.MIRROR_SPRITE_INFO, all_borders=True)
        self.initialize_sprites(util.MIRROR_SPRITE_INFO)
        self._geometry_segments[0].is_reflective = True
        self._geometry_segments[0].calculate_normal()
        self._geometry_segments[2].is_reflective = True
        self._geometry_segments[2].calculate_normal()


class Lens(WorldObject):
    def __init__(self, position: numpy.ndarray, rotation_angle: float):
        super().__init__(position, rotation_angle)
        radius_of_curvature = 110
        coverage_angle = numpy.pi / 5
        short_axis = (
            numpy.array([math.cos(rotation_angle), math.sin(rotation_angle)])
            * math.cos(coverage_angle / 2)
            * radius_of_curvature
        )
        self._geometry_segments = [
            geometry.Arc(
                self,
                position - short_axis,
                radius_of_curvature,
                rotation_angle,
                coverage_angle,
            ),
            geometry.Arc(
                self,
                position + short_axis,
                radius_of_curvature,
                numpy.pi + rotation_angle,
                coverage_angle,
            ),
        ]


class LightSource(WorldObject):
    def __init__(self, position: numpy.ndarray, rotation_angle: float):
        super().__init__(position, rotation_angle)
        self.light_rays = [
            light.LightRay(numpy.zeros(2), numpy.zeros(2))
            for _ in range(util.NUM_LIGHT_RAYS)
        ]

    def move(self, move_distance: numpy.ndarray, rotate_angle: float = 0):
        super().move_geometry(move_distance, rotate_angle)
        self.calculate_light_ray_positions()

    def draw(self):
        alpha = int(32 + 32 * math.sin(2.5 * time.time()))
        for ray in self.light_rays:
            ray.draw(alpha)
        super().draw()

    @abstractmethod
    def calculate_light_ray_positions(self):
        pass


class RadialLightSource(LightSource):
    def __init__(self, position: numpy.ndarray, rotation_angle: float, angular_spread: float):
        super().__init__(position, rotation_angle)
        self.initialize_geometry(util.SOURCE_SPRITE_INFO, all_borders=False)
        self.initialize_sprites(util.SOURCE_SPRITE_INFO)
        self._angular_spread = angular_spread
        self.calculate_light_ray_positions()

    def calculate_light_ray_positions(self):
        num_rays = len(self.light_rays)
        for n in range(num_rays):
            ray_angle = (n / num_rays) * (
                self._rotation_angle - self._angular_spread / 2
            ) + (1 - n / num_rays) * (self._rotation_angle + self._angular_spread / 2)
            ray_direction = numpy.array([math.cos(ray_angle), math.sin(ray_angle)])
            self.light_rays[n]._origin = self._position
            self.light_rays[n]._direction = ray_direction


class ParallelLightSource(LightSource):
    def __init__(self, position: numpy.ndarray, rotation_angle: float):
        super().__init__(position, rotation_angle)
        self.initialize_geometry(util.SOURCE_SPRITE_INFO, all_borders=False)
        self.initialize_sprites(util.SOURCE_SPRITE_INFO)
        self._width = util.SOURCE_SPRITE_INFO[1] * util.SOURCE_SPRITE_INFO[2]
        self.calculate_light_ray_positions()

    def calculate_light_ray_positions(self):
        num_rays = len(self.light_rays)
        ray_direction = numpy.array(
            [math.cos(self._rotation_angle), math.sin(self._rotation_angle)]
        )
        spread_direction = numpy.array(
            [
                math.cos(self._rotation_angle + 0.5 * numpy.pi),
                math.sin(self._rotation_angle + 0.5 * numpy.pi),
            ]
        )
        for n in range(num_rays):
            self.light_rays[n]._origin = (
                self._position
                - (self._width * (n / (util.NUM_LIGHT_RAYS - 1) - 0.5))
                * spread_direction
            )
            self.light_rays[n]._direction = ray_direction


class LightReceiver(WorldObject):
    def __init__(self, position: numpy.ndarray, rotation_angle: float):
        super().__init__(position, rotation_angle)
        self.initialize_geometry(util.SOURCE_SPRITE_INFO, all_borders=False)
        self.initialize_sprites(util.SOURCE_SPRITE_INFO)
        self._geometry_segments[0].is_receiver = True
        self._geometry_segments[1].is_receiver = True
        self.charge = 0

    def draw(self):
        color = min(255 * self.charge / util.RECEIVER_THRESHOLD, 255)
        for sprite in self._sprite_list:
            sprite.color = (color, color, 70)
        super().draw()
