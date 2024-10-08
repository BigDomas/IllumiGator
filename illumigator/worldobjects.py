import math
import time
from abc import abstractmethod

import arcade
import numpy

from illumigator import geometry, light, object_animation, util


class WorldObject:

    def __init__(
        self,
        position: numpy.ndarray,
        rotation_angle: float, *,
        is_interactable=False,
    ):
        self.position: numpy.ndarray = position
        self.rotation_angle: float = rotation_angle
        self.is_interactable: bool = is_interactable
        self.geometry_segments: list[geometry.Geometry] = []
        self.obj_animation: object_animation.ObjectAnimation | None = None

        self._sprite_list: arcade.SpriteList = arcade.SpriteList()

    def initialize_sprites(self, sprite_info: tuple, *, dimensions: numpy.ndarray | None = None):
        sprite_path, sprite_scale, sprite_width, sprite_height = sprite_info
        self._sprite_list = arcade.SpriteList()
        if dimensions is None:
            self._sprite_list.append(
                util.load_sprite(
                    sprite_path,
                    sprite_scale,
                    image_width=sprite_width,
                    image_height=sprite_height,
                    center_x=self.position[0],
                    center_y=self.position[1],
                    angle=numpy.rad2deg(self.rotation_angle),
                    hit_box_algorithm="Simple",
                )
            )

        else:
            axis1_norm = numpy.array([math.cos(self.rotation_angle), math.sin(self.rotation_angle)])
            axis2_norm = numpy.array([-math.sin(self.rotation_angle), math.cos(self.rotation_angle)])
            axis1 = 0.5 * sprite_width * sprite_scale * dimensions[0] * axis1_norm
            axis2 = 0.5 * sprite_height * sprite_scale * dimensions[1] * axis2_norm

            for col in range(int(dimensions[0])):
                for row in range(int(dimensions[1])):
                    sprite_center = (self.position - axis1 - axis2) + sprite_scale * (
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
                            angle=numpy.rad2deg(self.rotation_angle),
                            hit_box_algorithm="Simple",
                        )
                    )

    def initialize_geometry(
        self, sprite_info: tuple, *, dimensions: numpy.ndarray = numpy.ones(2),
        all_borders: bool = False, spokes: int = 0,
        is_reflective: bool = False, is_refractive: bool = False, is_receiver: bool = False, is_enemy: bool = False
    ):
        sprite_path, sprite_scale, sprite_width, sprite_height = sprite_info
        axis1_norm = numpy.array([math.cos(self.rotation_angle), math.sin(self.rotation_angle)])
        axis2_norm = numpy.array([-math.sin(self.rotation_angle), math.cos(self.rotation_angle)])
        axis1 = 0.5 * sprite_width * sprite_scale * dimensions[0] * axis1_norm
        axis2 = 0.5 * sprite_height * sprite_scale * dimensions[1] * axis2_norm
        if all_borders is True:
            self.geometry_segments = [
                geometry.Line(self, self.position - axis1 - axis2, self.position - axis1 + axis2, is_reflective, is_refractive, is_receiver, is_enemy),
                geometry.Line(self, self.position - axis1 + axis2, self.position + axis1 + axis2, is_reflective, is_refractive, is_receiver, is_enemy),
                geometry.Line(self, self.position + axis1 + axis2, self.position + axis1 - axis2, is_reflective, is_refractive, is_receiver, is_enemy),
                geometry.Line(self, self.position + axis1 - axis2, self.position - axis1 - axis2, is_reflective, is_refractive, is_receiver, is_enemy),
            ]
        elif spokes != 0:
            self.geometry_segments = []
            for _ in range(spokes):
                self.geometry_segments.append(
                    geometry.Line(self, self.position + axis1, self.position - axis1, is_reflective, is_refractive, is_receiver, is_enemy)
                )
                axis1 = util.rotate(axis1, numpy.pi / spokes)
        else:  # Only do the diagonals
            self.geometry_segments = [
                geometry.Line(self, self.position - axis1 - axis2, self.position + axis1 + axis2, is_reflective, is_refractive, is_receiver, is_enemy),
                geometry.Line(self, self.position - axis1 + axis2, self.position + axis1 - axis2, is_reflective, is_refractive, is_receiver, is_enemy),
            ]


    def draw(self):
        self._sprite_list.draw(pixelated=True)
        if util.DEBUG_GEOMETRY is True:
            for segment in self.geometry_segments:
                segment.draw(thickness=2)

    def distance_squared_to_center(self, point_x, point_y):
        return util.distance_squared(self.position, numpy.array([point_x, point_y]))

    def check_collision_with_point(self, point: numpy.ndarray):
        for sprite in self._sprite_list:
            if sprite.collides_with_point(point):
                return True
        else:
            return False

    def check_collision_with_sprite(self, sprite: arcade.Sprite):
        return sprite.collides_with_list(self._sprite_list)

    def move_geometry(self, move_distance: numpy.ndarray = numpy.zeros(2), rotate_angle: float = 0):
        for segment in self.geometry_segments:
            segment.move(self.position, move_distance, rotate_angle=rotate_angle)
        self.position = self.position + move_distance
        self.rotation_angle = self.rotation_angle + rotate_angle

    def move_if_safe(
        self,
        character,
        enemy,
        move_distance: numpy.ndarray = numpy.zeros(2),
        rotate_angle: float = 0,
        ignore_checks: bool = False
    ) -> bool:
        for sprite in self._sprite_list:
            new_position = (
                util.rotate_around_point(
                    self.position,
                    numpy.array([sprite.center_x, sprite.center_y]),
                    rotate_angle,
                )
                + move_distance
            )
            sprite.radians += rotate_angle
            sprite.center_x, sprite.center_y = new_position[0], new_position[1]
        if not ignore_checks and (
                self.check_collision_with_sprite(character.sprite) or (enemy is not None and self.check_collision_with_sprite(enemy.sprite))
        ):
            for sprite in self._sprite_list:
                new_position = util.rotate_around_point(
                    self.position,
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
            self.position,
            self.position + travel,
            dt,
            angle1=self.rotation_angle,
            angle2=self.rotation_angle + angle_travel,
        )

    def apply_object_animation(self, character, enemy):
        # Test for sprite collisions
        animation_data = self.obj_animation.get_new_position()
        position_change = animation_data[0] - self.position
        angle_change = animation_data[1] - self.rotation_angle
        if not self.move_if_safe(
            character, enemy, move_distance=position_change, rotate_angle=angle_change
        ):  # If move is unsafe
            self.obj_animation.backtrack()


class Wall(WorldObject):
    def __init__(self, position: numpy.ndarray, dimensions: numpy.ndarray, rotation_angle: float):
        super().__init__(position, rotation_angle, is_interactable=False)
        self.dimensions = dimensions
        self.initialize_geometry(util.WALL_SPRITE_INFO, dimensions=dimensions)
        self.initialize_sprites(util.WALL_SPRITE_INFO, dimensions=dimensions)


class Mirror(WorldObject):
    def __init__(self, position: numpy.ndarray, rotation_angle: float):
        super().__init__(position, rotation_angle, is_interactable=True)
        self.initialize_geometry(util.MIRROR_SPRITE_INFO, all_borders=True)
        self.initialize_sprites(util.MIRROR_SPRITE_INFO)
        self.geometry_segments[0].is_reflective = True
        self.geometry_segments[0].calculate_normal()
        self.geometry_segments[2].is_reflective = True
        self.geometry_segments[2].calculate_normal()

    def draw_outline(self):
        thickness = int(4 + 2 * math.sin(15 * time.time()))
        for segment in self.geometry_segments:
            segment.draw(thickness=thickness, color=arcade.color.RED)


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
        self.geometry_segments = [
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
        self.initialize_sprites(util.LENS_SPRITE_INFO)


class LightSource(WorldObject):
    def __init__(self, position: numpy.ndarray, rotation_angle: float):
        super().__init__(position, rotation_angle)
        self.light_rays = [
            light.LightRay(numpy.zeros(2), numpy.zeros(2))
            for _ in range(util.NUM_LIGHT_RAYS)
        ]

    def move(self, move_distance: numpy.ndarray, rotate_angle: float = 0):
        super().move_geometry(move_distance, rotate_angle)
        self._sprite_list[0].center_x = self.position[0]
        self._sprite_list[0].center_y = self.position[1]
        self.calculate_light_ray_positions()

    def draw(self):
        alpha = int(25 + 15 * math.sin(4 * time.time()))
        for ray in self.light_rays:
            ray.draw(alpha)
        super().draw()

    @abstractmethod
    def calculate_light_ray_positions(self):
        pass


class RadialLightSource(LightSource):
    def __init__(self, position: numpy.ndarray, rotation_angle: float, angular_spread: float):
        super().__init__(position, rotation_angle)
        self.initialize_sprites(util.SOURCE_SPRITE_INFO)
        self._angular_spread = angular_spread
        self.calculate_light_ray_positions()

    def calculate_light_ray_positions(self):
        num_rays = len(self.light_rays)
        for n in range(num_rays):
            ray_angle = (n / num_rays) * (
                    self.rotation_angle - self._angular_spread / 2
            ) + (1 - n / num_rays) * (self.rotation_angle + self._angular_spread / 2)
            ray_direction = numpy.array([math.cos(ray_angle), math.sin(ray_angle)])
            self.light_rays[n].origin = self.position
            self.light_rays[n].direction = ray_direction


class ParallelLightSource(LightSource):
    def __init__(self, position: numpy.ndarray, rotation_angle: float):
        super().__init__(position, rotation_angle)
        self.initialize_sprites(util.SOURCE_SPRITE_INFO)
        self.width = util.SOURCE_SPRITE_INFO[1] * util.SOURCE_SPRITE_INFO[2] - 7
        self.calculate_light_ray_positions()

    def calculate_light_ray_positions(self):
        num_rays = len(self.light_rays)
        ray_direction = numpy.array([
            math.cos(self.rotation_angle),
            math.sin(self.rotation_angle)
        ])
        spread_direction = numpy.array([
            math.cos(self.rotation_angle + numpy.pi / 2),
            math.sin(self.rotation_angle + numpy.pi / 2),
        ])
        for n in range(num_rays):
            self.light_rays[n].origin = (
                self.position
                - spread_direction * (self.width * (n / (util.NUM_LIGHT_RAYS - 1) - 0.5))
            )
            self.light_rays[n].direction = ray_direction


class LightReceiver(WorldObject):
    def __init__(self, position: numpy.ndarray, rotation_angle: float, planet: str = "moon"):
        super().__init__(position, rotation_angle)
        self.initialize_geometry(util.RECEIVER_SPRITE_INFO, spokes=4, is_receiver=True)
        self.initialize_sprites((planet+".png",) + util.RECEIVER_SPRITE_INFO[1:])
        self._sprite_list.append(
            util.load_sprite(planet +"_exploded.png",
                util.RECEIVER_SPRITE_INFO[1],
                image_width=util.RECEIVER_SPRITE_INFO[2],
                image_height=util.RECEIVER_SPRITE_INFO[3],
                center_x=self.position[0],
                center_y=self.position[1])
        )
        self._sprite_list[1].visible = False
        self.planet = planet
        self.charge = 0

    def draw(self):
        # color = min(255 * self.charge / util.RECEIVER_THRESHOLD, 255)
        color = max(255 * (1.0 - self.charge / util.RECEIVER_THRESHOLD), 0)

        if self.charge >= util.RECEIVER_THRESHOLD - 0.01:
            self._sprite_list[0].visible = False
            self._sprite_list[1].visible = True

        for sprite in self._sprite_list:
            sprite.color = (255, color, color)

        super().draw()



def find_nearest_world_object(point: numpy.ndarray, world_objects: list) -> tuple:
    nearest_distance_squared = float('inf')
    nearest_world_object = None
    for wo in world_objects:
        distance_squared = util.distance_squared(wo.position, point)
        if distance_squared < nearest_distance_squared:
            nearest_distance_squared = distance_squared
            nearest_world_object = wo
    return nearest_world_object, nearest_distance_squared