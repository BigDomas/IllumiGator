import math
import time

import arcade
import numpy


class LightRay:
    def __init__(self, origin, direction, generation=0):
        self._origin = origin
        self._direction = direction
        self._end = numpy.zeros(2)
        self._child_ray: LightRay | None = None
        self._generation = generation
        self._flicker = 20

    def _generate_child_ray(self, direction):
        if self._child_ray is None:
            self._child_ray = LightRay(
                self._end + direction * 0.001,
                direction,
                generation=self._generation + 1,
            )
        else:
            self._child_ray._origin = self._end + direction * 0.001
            self._child_ray._direction = direction

    def draw(self, alpha):
        color = (255, 255, 255, alpha + self._flicker)
        arcade.draw_line(*self._origin, *self._end, color=color, line_width=6)
        arcade.draw_line(*self._origin, *self._end, color=color, line_width=4)
        arcade.draw_line(*self._origin, *self._end, color=color, line_width=3)
        if self._child_ray is not None:
            self._child_ray.draw(alpha)


def get_raycast_results(ray_p1, ray_p2, line_p1, line_p2) -> tuple[numpy.ndarray, numpy.ndarray]:  # distances, line indices
    # Don't @ me...    https://en.wikipedia.org/wiki/Line-line_intersection#Given_two_points_on_each_line_segment
    ray_dx_dy = -ray_p2.T
    line_dx_dy = numpy.array(((line_p1[:, 0] - line_p2[:, 0]), (line_p1[:, 1] - line_p2[:, 1])))
    x_dif = numpy.subtract.outer(line_p1[:, 0], ray_p1[:, 0])
    y_dif = numpy.subtract.outer(line_p1[:, 1], ray_p1[:, 1])

    denominators = numpy.multiply.outer(line_dx_dy[0], ray_dx_dy[1]) - numpy.multiply.outer(line_dx_dy[1], ray_dx_dy[0])
    t = numpy.where(
        denominators != 0,
        (x_dif * ray_dx_dy[1] - y_dif * ray_dx_dy[0]) / denominators,
        float('inf')
    )
    u = numpy.where(
        denominators != 0,
        (x_dif.T * line_dx_dy[1] - y_dif.T * line_dx_dy[0]).T / denominators,
        float('inf')
    )

    u[(u < 0) | (t < 0) | (t > 1)] = float('inf')  # u
    min_indices = numpy.argmin(u, axis=0)

    return u.T[:, min_indices].diagonal(), min_indices

def get_arc_raycast_results(ray_x1, ray_y1, ray_x2, ray_y2, arc_x, arc_y, arc_r, arc_angle1, arc_angle2) -> numpy.ndarray:  # distances, line indices
    # Don't @ me...    https://en.wikipedia.org/wiki/Line-sphere_intersection#Calculation_using_vectors_in_3D
    ray_origins = numpy.array((ray_x1, ray_y1)).T
    ray_dx_dy = numpy.array((ray_x2, ray_y2))
    diff_x = numpy.subtract.outer(ray_x1, arc_x).T
    diff_y = numpy.subtract.outer(ray_y1, arc_y).T
    temp_calculation1 = numpy.multiply(ray_dx_dy[0], diff_x) + numpy.multiply(ray_dx_dy[1], diff_y)
    temp_calculation2 = numpy.linalg.norm(numpy.array([diff_x, diff_y]), axis=0)

    nabla = (temp_calculation1 * temp_calculation1) - (
                numpy.subtract((temp_calculation2 * temp_calculation2).T, arc_r * arc_r).T
            )
    nabla_sqrt = numpy.where(nabla >= 0, numpy.sqrt(nabla), -1)

    intersection_distance1 = numpy.where(
        nabla_sqrt != -1,
        -nabla_sqrt - temp_calculation1,
        -1)
    point1_x = numpy.where(
        intersection_distance1 > 0,
        ray_origins.T[0] + ray_dx_dy[0] * intersection_distance1,
        float('inf'))
    point1_y = numpy.where(
        intersection_distance1 > 0,
        ray_origins.T[1] + ray_dx_dy[1] * intersection_distance1,
        float('inf'))
    point1_angle = numpy.arctan2(
        point1_y.T - arc_y,
        point1_x.T - arc_x
    )
    intersection_distance1 = numpy.where(
        (intersection_distance1.T > 0) &
        (((arc_angle1 < point1_angle) & (point1_angle < arc_angle2)) | (
            (arc_angle2 < arc_angle1) & (
                ((0 <= arc_angle1) & (arc_angle1 <= point1_angle)) |
                ((point1_angle <= arc_angle2) & (arc_angle2 <= 0))
            )
        )),
        intersection_distance1.T,
        float('inf')
    ).T

    intersection_distance2 = numpy.where(
            nabla_sqrt != -1,
            nabla_sqrt - temp_calculation1,
            -1)
    point2_x = numpy.where(
        intersection_distance2 > 0,
        ray_origins.T[0] + ray_dx_dy[0] * intersection_distance2,
        float('inf'))
    point2_y = numpy.where(
        intersection_distance2 > 0,
        ray_origins.T[1] + ray_dx_dy[1] * intersection_distance2,
        float('inf'))
    point2_angle = numpy.where(
        point2_x.T != float('inf'),
        numpy.arctan2(
            point2_y.T - arc_y,
            point2_x.T - arc_x
        ),
        float('inf')
    )
    intersection_distance2 = numpy.where(
        (intersection_distance2.T > 0) &
        (((arc_angle1 < point2_angle) & (point2_angle < arc_angle2)) | (
            (arc_angle2 < arc_angle1) & (
                ((0 <= arc_angle1) & (arc_angle1 <= point2_angle)) |
                ((point2_angle <= arc_angle2) & (arc_angle2 <= 0))
            )
        )),
        intersection_distance2.T,
        float('inf')
    ).T

    return numpy.where(
        numpy.min(intersection_distance1, axis=0) < numpy.min(intersection_distance2, axis=0),
        [numpy.min(intersection_distance1, axis=0), numpy.argmin(intersection_distance1, axis=0)],
        [numpy.min(intersection_distance2, axis=0), numpy.argmin(intersection_distance2, axis=0)]
    )
