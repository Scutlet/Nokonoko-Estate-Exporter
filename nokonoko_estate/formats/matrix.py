from copy import copy
import math
from typing import Self


class RotationMatrix:
    """A 3x3 rotation matrix that does not support translations"""

    # fmt: off
    ListMatrix = tuple[
        float, float, float,
        float, float, float,
        float, float, float,
    ]
    # fmt: on

    def __init__(self, matrix: ListMatrix):
        """Creates a rotation matrix given some XYZ-Euler angles. Assumes Z-up right-handed coordinates."""
        self._matrix = matrix

    @classmethod
    def from_euler(cls, rot: tuple[int, int, int], scale: tuple[int, int, int]) -> Self:
        """Compute a transformation matrix given some XYZ-Euler angles. Assumes Z-up right-handed coordinates."""
        rot_x, rot_y, rot_z = (
            math.radians(rot[0]),
            math.radians(rot[1]),
            math.radians(rot[2]),
        )

        # fmt: off
        mat_x = RotationMatrix([
            1, 0, 0,
            0, math.cos(rot_x), -math.sin(rot_x),
            0, math.sin(rot_x), math.cos(rot_x),
        ])
        mat_y = RotationMatrix([
            math.cos(rot_y), 0, math.sin(rot_y),
            0, 1, 0,
            -math.sin(rot_y), 0, math.cos(rot_y),
        ])
        mat_z = RotationMatrix([
            math.cos(rot_z), -math.sin(rot_z), 0,
            math.sin(rot_z), math.cos(rot_z), 0,
            0, 0, 1,
        ])
        mat_scale = RotationMatrix([
            scale[0], 0, 0,
            0, scale[1], 0,
            0, 0, scale[2],
        ])

        # Multiply matrices (extrinsic rotation, so in order z-x-y-scale as matrix multiplication is non-commutative)
        matrix = mat_z * mat_y
        matrix = matrix * mat_x
        matrix = matrix * mat_scale
        return matrix

    def __mul__(self, other) -> Self:
        """Multiplies two 3x3 rotation matrices together. The result is a new rotation matrix"""
        if not isinstance(other, RotationMatrix):
            raise ValueError(f"{other} is not a Rotation Matrix")

        res = RotationMatrix([0] * 9)
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    res._matrix[3 * i + j] += (
                        self._matrix[3 * i + k] * other._matrix[3 * k + j]
                    )

        return res


class TransformationMatrix:
    """A 4x4 rotation matrix that also supports translations"""

    # fmt: off
    ListMatrix = tuple[
        float, float, float, float,
        float, float, float, float,
        float, float, float, float,
        float, float, float, float,
    ]
    # fmt: on

    def __init__(self, matrix: ListMatrix):
        self._matrix = matrix

    @classmethod
    def from_rotation_matrix(
        cls, matrix: RotationMatrix, translate: tuple[float, float, float]
    ) -> Self:
        # Add translation to matrix (doesn't affect orientation)
        # fmt: off
        mtx = cls([
            *matrix._matrix[0:3], translate[0],
            *matrix._matrix[3:6], translate[1],
            *matrix._matrix[6:9], translate[2],
            0, 0, 0, 1,
        ])
        return mtx
        # fmt: on

    @classmethod
    def identity(self) -> Self:
        """Provides a 4x4 identity matrix"""
        # fmt: off
        return TransformationMatrix([1, 0, 0, 0,
                                     0, 1, 0, 0,
                                     0, 0, 1, 0,
                                     0, 0, 0, 1])
        # fmt: on

    def round(self, decimal_places=6) -> Self:
        """Rounds the matrix values to a given amount of decimal places. Modifies the matrix in-place"""
        self._matrix = [round(i, decimal_places) for i in self._matrix]
        return self

    def as_raw(self):
        """Return the raw matrix values"""
        return copy(self._matrix)

    def __str__(self):
        res = ""
        for i in range(16):
            res += f"{self._matrix[i]: <24} "
            if i % 4 == 3:
                res += "\n"
        return res

    def __mul__(self, other) -> Self:
        """Multiplies two 4x4 rotation matrices together. The result is a new transformation matrix"""
        if not isinstance(other, TransformationMatrix):
            raise ValueError(f"{other} is not a Transformation Matrix")

        res = TransformationMatrix([0] * 16)
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    res._matrix[4 * i + j] += (
                        self._matrix[4 * i + k] * other._matrix[4 * k + j]
                    )
        return res
