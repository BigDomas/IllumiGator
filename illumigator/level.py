import numpy

from illumigator import worldobjects, entity, util, light

BORDER_WALLS = [
    worldobjects.Wall(
        numpy.array([util.WALL_SIZE / 2, 720 / 2]),
        numpy.array([1, 720 / util.WALL_SIZE]),
        0),
    worldobjects.Wall(
        numpy.array([1280 - util.WALL_SIZE / 2, 720 / 2]),
        numpy.array([1, 720 / util.WALL_SIZE]),
        0),
    worldobjects.Wall(
        numpy.array([1280 / 2, util.WALL_SIZE / 2]),
        numpy.array([1280 / util.WALL_SIZE - 2, 1]),
        0),
    worldobjects.Wall(
        numpy.array([1280 / 2, 720 - util.WALL_SIZE / 2]),
        numpy.array([1280 / util.WALL_SIZE - 2, 1]),
        0)
]

class Level:
    def __init__(
            self,
            wall_coordinate_list: list[list] = None,
            mirror_coordinate_list: list[list] = None,
            light_receiver_coordinate_list: list[list] = None,
            light_source_coordinate_list: list[list] = None,
            animated_wall_coordinate_list: list[list] = None,
            lens_coordinate_list: list[list] = None,
            gator_coordinates: list = None,
            enemy_coordinates: list = None,
            name="default",
            background="space",
            planet="moon",
            walking_volume=1
    ):

        if name == "Level 1":
            background = "level1_background"

        self.background = background + ".png"
        self.background_sprite = util.load_sprite(self.background, scale=2/3, center_x=util.WORLD_WIDTH // 2, center_y=util.WORLD_HEIGHT // 2)
        self.background_sprite.alpha = 100
        self.planet = planet
        self.name = name

        self.wall_list = [
            worldobjects.Wall(
                numpy.array([
                    wall_coordinates[0],
                    wall_coordinates[1]
                ]),
                numpy.array([
                    wall_coordinates[2],
                    wall_coordinates[3]
                ]),
                wall_coordinates[4],
            ) for wall_coordinates in wall_coordinate_list
        ]
        self.wall_list.extend(BORDER_WALLS)

        self.mirror_list = [
            worldobjects.Mirror(
                numpy.array([
                    mirror_coordinates[0], mirror_coordinates[1]
                ]),
                mirror_coordinates[2],
            ) for mirror_coordinates in mirror_coordinate_list
        ]

        self.lens_list = [
            worldobjects.Lens(
                numpy.array([
                    lens_coordinates[0],
                    lens_coordinates[1]
                ]),
                lens_coordinates[2]
            ) for lens_coordinates in lens_coordinate_list
        ]

        self.light_receiver_list = [
            worldobjects.LightReceiver(
                numpy.array([
                    light_receiver_coordinates[0], light_receiver_coordinates[1]
                ]),
                light_receiver_coordinates[2],
                planet=self.planet
            ) for light_receiver_coordinates in light_receiver_coordinate_list
        ]

        self.light_source_list = []
        for light_source_coordinates in light_source_coordinate_list:
            if len(light_source_coordinates) == 4:  # Has an angular spread argument
                self.light_source_list.append(
                    worldobjects.RadialLightSource(
                        numpy.array(
                            [light_source_coordinates[0], light_source_coordinates[1]]
                        ),
                        light_source_coordinates[2],
                        light_source_coordinates[3],
                    )
                )
            else:
                self.light_source_list.append(
                    worldobjects.ParallelLightSource(
                        numpy.array(
                            [light_source_coordinates[0], light_source_coordinates[1]]
                        ),
                        light_source_coordinates[2],
                    )
                )

        self.animated_wall_list = []
        for animated_wall_coordinates in animated_wall_coordinate_list:
            self.wall_list.append(
                worldobjects.Wall(
                    numpy.array([
                        animated_wall_coordinates[0],
                        animated_wall_coordinates[1]
                    ]),
                    numpy.array([
                        animated_wall_coordinates[2],
                        animated_wall_coordinates[3]
                    ]),
                    animated_wall_coordinates[4]
                )
            )
            self.wall_list[-1].create_animation(
                numpy.array([animated_wall_coordinates[5], animated_wall_coordinates[6]]),
                animated_wall_coordinates[7], animated_wall_coordinates[8])

        self.entity_world_object_list: list[worldobjects.WorldObject] = []
        if len(enemy_coordinates) == 0:
            self.enemy = None
        else:
            self.enemy = entity.Enemy(enemy_coordinates)
            self.entity_world_object_list.append(self.enemy.world_object)
        self.gator = entity.Gator(gator_coordinates, walking_volume)
        self.entity_world_object_list.append(self.gator.world_object)


        #  Append line segments and arcs to geometry lists
        self.line_segments = []
        self.arcs = []
        for world_object in (self.entity_world_object_list + self.wall_list + self.mirror_list + self.light_receiver_list):
            self.line_segments.extend(world_object.geometry_segments)
        for world_object in self.lens_list:
            self.arcs.extend(world_object.geometry_segments)


    def update(self, walking_volume):
        if self.gator.update(self, walking_volume, self.enemy) is False:
            return False
        if self.enemy is not None:
            self.enemy.update(self, self.gator)

        for wall in self.wall_list:
            if wall.obj_animation is not None:
                wall.apply_object_animation(self.gator, self.enemy)

        for light_receiver in self.light_receiver_list:
            light_receiver.charge *= util.CHARGE_DECAY

        #  ==================== Raycasting and update rays ====================
        line_p1 = numpy.ndarray((len(self.line_segments), 2))
        line_p2 = numpy.ndarray((len(self.line_segments), 2))
        for line_i in range(len(self.line_segments)):
            line_p1[line_i], line_p2[line_i] = self.line_segments[line_i]._point1, self.line_segments[line_i]._point2
        arc_center = numpy.ndarray((len(self.arcs), 2))
        arc_radius = numpy.ndarray((len(self.arcs),))
        arc_angles = numpy.ndarray((len(self.arcs), 2))
        for arc_i in range(len(self.arcs)):
            arc_center[arc_i], arc_radius[arc_i], arc_angles[arc_i][0], arc_angles[arc_i][1] = self.arcs[arc_i].center, self.arcs[arc_i].radius, self.arcs[arc_i]._start_angle, self.arcs[arc_i]._end_angle

        for light_source in self.light_source_list:
            ray_queue = light_source.light_rays[:]
            queue_length = len(ray_queue)
            while queue_length > 0:
                ray_origin = numpy.ndarray((queue_length, 2))
                ray_dir = numpy.ndarray((queue_length, 2))
                for ray_i in range(queue_length):
                    ray_origin[ray_i], ray_dir[ray_i] = ray_queue[ray_i].origin, ray_queue[ray_i].direction

                nearest_line_distances, nearest_line_indices = light.get_line_raycast_results(ray_origin, ray_dir, line_p1, line_p2)

                if len(self.arcs) > 0:
                    nearest_arc_distance, nearest_arc_indices = light.get_arc_raycast_results(
                        ray_origin[:, 0], ray_origin[:, 1], ray_dir[:, 0], ray_dir[:, 1], arc_center[:, 0], arc_center[:, 1],
                        arc_radius, arc_angles[:, 0], arc_angles[:, 1])
                else:
                    nearest_arc_distance, nearest_arc_indices = numpy.full_like(nearest_line_distances, float('inf')), numpy.full_like(nearest_line_distances, -1)

                for i in range(queue_length):
                    ray = ray_queue[i]
                    if nearest_line_distances[i] <= nearest_arc_distance[i]:
                        ray._end = ray.origin + ray.direction * nearest_line_distances[i]
                        nearest_line = self.line_segments[int(nearest_line_indices[i])]
                        if nearest_line.is_reflective and ray.generation < util.MAX_GENERATIONS:  # if the ray hit a mirror, create child and cast it
                            ray._generate_child_ray(
                                ray.direction - (2 * nearest_line._normal * (nearest_line._normal @ ray.direction))
                            )
                            ray_queue.append(ray.child_ray)
                        elif nearest_line.is_receiver:  # Charge receiver when a light ray hits it
                            nearest_line.parent_object.charge += util.LIGHT_INCREMENT
                        elif nearest_line.is_enemy and self.enemy.status != "aggro":
                            self.enemy.status = "aggro"
                            self.enemy.update_geometry_shape()
                            ray.child_ray = None
                        else:
                            ray.child_ray = None
                    else:
                        ray._end = ray.origin + ray.direction * nearest_arc_distance[i]
                        nearest_arc = self.arcs[int(nearest_arc_indices[i])]
                        if nearest_arc.is_refractive and ray.generation < util.MAX_GENERATIONS:  # if the ray hit a lens, create child and cast it
                            try:
                                ray._generate_child_ray(nearest_arc.get_refracted_direction(ray))
                                ray_queue.append(ray.child_ray)
                            except:
                                ray.child_ray = None
                        else:
                            ray.child_ray = None

                ray_queue = ray_queue[queue_length:]
                queue_length = len(ray_queue)

        if self.gator.status == "dead":
            # Show dead animations
            self.gator.left_character_loader.dead = True
            self.gator.right_character_loader.dead = True
            self.enemy.status = "player_dead"
            # self.game_state = "game_over"

    def draw(self):
        self.background_sprite.draw(pixelated=True)
        for light_source in self.light_source_list:
            light_source.draw()
        for wall in self.wall_list:
            wall.draw()
        for mirror in self.mirror_list:
            mirror.draw()
        for lens in self.lens_list:
            lens.draw()
        for light_receiver in self.light_receiver_list:
            light_receiver.draw()
        self.gator.draw()
        if self.enemy is not None:
            self.enemy.draw()

    def check_collisions(self, character: entity.Gator):
        for wo in (self.wall_list + self.mirror_list + self.lens_list + self.light_receiver_list + self.light_source_list):
            if wo.check_collision(character.sprite):
                return True
        else:
            return False


def load_level(level: dict, walking_volume) -> Level:
    level_data = level["level_data"]
    return Level(
        level_data["wall_coordinate_list"],
        level_data["mirror_coordinate_list"],
        level_data["light_receiver_coordinate_list"],
        level_data["light_source_coordinate_list"],
        level_data["animated_wall_coordinate_list"],
        level_data["lens_coordinate_list"],
        level_data["gator_coordinates"],
        level_data["enemy_coordinates"],
        level["level_name"],
        planet=level["planet"],
        walking_volume=walking_volume
    )

class LevelCreator:
    def __init__(self, level):
        self.level = level
        self.selected_world_object = None
        self.selected_world_object_list = None
        self.snap_to_grid = True

    def generate_object(self, type_selection: int, mouse_position):
        new_world_object = None
        new_world_object_list = None
        match type_selection:
            case 1:  # Wall
                new_world_object = worldobjects.Wall(mouse_position, numpy.ones(2), 0)
                new_world_object_list = self.level.wall_list
                print("Wall")
            case 2:  # Mirror
                new_world_object = worldobjects.Mirror(mouse_position, 0)
                new_world_object_list = self.level.mirror_list
                print("Mirror")
            case 3:  # Lens
                new_world_object = worldobjects.Lens(mouse_position, 0)
                new_world_object_list = self.level.lens_list
                print("Lens")
            case 4:  # Source
                new_world_object = worldobjects.ParallelLightSource(mouse_position, 0)
                new_world_object_list = self.level.light_source_list
                print("Source")
            case 5:  # Receiver
                new_world_object = worldobjects.LightReceiver(mouse_position, 0)
                new_world_object_list = self.level.light_source_list
                print("Receiver")

        if self.selected_world_object is not None:
            self.selected_world_object_list.remove(self.selected_world_object)
        self.selected_world_object = new_world_object
        self.selected_world_object_list = new_world_object_list
        new_world_object_list.append(new_world_object)
