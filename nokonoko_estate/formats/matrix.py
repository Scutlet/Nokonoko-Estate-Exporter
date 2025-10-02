from copy import copy
import math
from typing import Generic, Literal, Self, TypeVar

N = TypeVar("N", bound=int)
M = TypeVar("M", bound=int)


class GenericMatrix(Generic[N, M]):
    """General interface for a matrix"""

    rows = 0
    columns = 0

    def __init__(self, matrix: tuple[float, ...], rows=None, columns=None):
        """Creates a rotation matrix given some XYZ-Euler angles."""
        if rows is not None:
            self.rows = rows
        if columns is not None:
            self.columns = columns
        assert (
            len(matrix) == self.rows * self.columns
        ), f"Cannot construct a Matrix[{self.rows}x{self.columns}] without defining all {self.rows*self.columns} components. Got {len(matrix)}"
        self._matrix = matrix

    @classmethod
    def identity(cls) -> Self:
        """Provides a rows*columns identity matrix"""
        assert (
            cls.rows == cls.columns
        ), "Cannot create an identity matrix when dimensions are not equal."
        matrix = [0] * cls.rows * cls.columns
        for i in range(cls.columns):
            matrix[cls.columns * i + i] = 1
        return cls(matrix, rows=cls.rows, columns=cls.columns)

    def round(self, decimal_places=6) -> Self:
        """Rounds the matrix values to a given amount of decimal places. Modifies the matrix in-place"""
        self._matrix = [round(i, decimal_places) for i in self._matrix]
        return self

    def as_raw(self):
        """Return the raw matrix values"""
        return copy(self._matrix)

    def transpose(self):
        """Transposes the matrix; flipping it on its diagonal. The result is a new rotation matrix"""
        if self.columns != self.rows:
            raise ValueError(
                f"Cannot transpose matrix; dimensions mismatch: Matrix[{self.rows}x{self.columns}]"
            )
        # fmt: off
        return GenericMatrix([
            self._matrix[i // self.columns + self.columns * (i % self.columns)] for i in range(len(self._matrix))
        ], rows=self.rows, columns=self.columns)
        # fmt: on

    def __mul__(self, other) -> "GenericMatrix":
        """Multiplies two matrices together. The result is a new rotation matrix"""
        if not isinstance(other, GenericMatrix):
            raise ValueError(f"{other} is not a Matrix")
        if self.columns != other.rows:
            raise ValueError(
                f"Cannot multiply matrices; dimensions mismatch: Matrix[{self.rows}x{self.columns}] * Matrix[{other.rows}x{other.columns}]"
            )
        res = GenericMatrix(
            [0] * (self.rows * other.columns), rows=self.rows, columns=other.columns
        )
        for i in range(self.rows):
            for j in range(other.columns):
                for k in range(self.columns):
                    res._matrix[other.columns * i + j] += (
                        self._matrix[self.columns * i + k]
                        * other._matrix[other.columns * k + j]
                    )
        return res

    def __str__(self):
        res = ""
        for i in range(len(self._matrix)):
            res += f"{self._matrix[i]: <24} "
            if i % self.columns == self.columns - 1:
                res += "\n"
        return res


class RotationMatrix(GenericMatrix[Literal[3], Literal[3]]):
    """A 3x3 rotation matrix that does not support translations. Assumes Z-up right-handed coordinates."""

    rows = 3
    columns = 3

    def inverse(self) -> Self:
        """Computes the inverse. This may be needed when the matrix is non-orthogonal (e.g. when scales/rotations are nested)"""
        # 0 a = ei - fh         48 - 57
        # 1 b = -(di - fg)      -(38 - 56)
        # 2 c = dh - eg         37 - 46
        # 3 d = -(bi - ch)      -(18 - 27)
        # 4 e = ai - cg         08 - 26
        # 5 f = -(ah - bg)      -(07 - 16)
        # 6 g = bf - ce         15 - 24
        # 7 h = -(af - cd)      -(05 - 23)
        # 8 i = ae - bd          04 - 13
        m = self._matrix
        a = m[4] * m[8] - m[5] * m[7]
        b = -(m[3] * m[8] - m[5] * m[6])
        c = m[3] * m[7] - m[4] * m[6]
        d = -(m[1] * m[8] - m[2] * m[7])
        e = m[0] * m[8] - m[2] * m[6]
        f = -(m[0] * m[7] - m[1] * m[6])
        g = m[1] * m[5] - m[2] * m[4]
        h = -(m[0] * m[5] - m[2] * m[3])
        i = m[0] * m[4] - m[1] * m[3]
        # det = 0*a + 1*b + 2*c
        det = m[0] * a + m[1] * b + m[2] * c

        assert det != 0, "Determinant of matrix is 0; cannot compute inverse!"

        # fmt: off
        return RotationMatrix([
            a / det, b / det, c / det,
            d / det, e / det, f / det,
            g / det, h / det, i / det
        ]).transpose()
        # fmt: on

    @classmethod
    def from_euler_rotation(cls, rot: tuple[int, int, int]) -> Self:
        """Computes a rotation matrix given XYZ-Euler angles."""
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

        # Multiply matrices (extrinsic rotation, so in order z-x-y-scale as matrix multiplication is non-commutative)
        matrix = mat_z * mat_y
        matrix = matrix * mat_x
        return matrix

    @classmethod
    def from_euler_scale(cls, scale: tuple[int, int, int]) -> Self:
        """Computes a rotation matrix given some scale."""
        # fmt: off
        return RotationMatrix([
            scale[0], 0, 0,
            0, scale[1], 0,
            0, 0, scale[2],
        ])
        # fmt: on

    @classmethod
    def from_euler(cls, rot: tuple[int, int, int], scale: tuple[int, int, int]) -> Self:
        """Compute a rotatoin matrix given some XYZ-Euler angles and scaling."""
        return cls.from_euler_rotation(rot) * cls.from_euler_scale(scale)

    @classmethod
    def from_euler_inverted(
        cls, rot: tuple[int, int, int], scale: tuple[int, int, int]
    ) -> Self:
        """Compute an inverted rotation matrix given some XYZ-Euler angles and scaling."""
        assert (
            scale[0] != 0 and scale[1] != 0 and scale[2] != 0
        ), f"Scale component cannot be zero {scale}"
        matrix_rot = cls.from_euler_rotation(rot).transpose()
        matrix_scale = cls.from_euler_scale((1 / scale[0], 1 / scale[1], 1 / scale[2]))
        return matrix_scale * matrix_rot


class TransformationMatrix(GenericMatrix[Literal[4], Literal[4]]):
    """A 4x4 rotation matrix that also supports translations"""

    rows = 4
    columns = 4

    def get_rotation_matrix(self) -> RotationMatrix:
        """Gets the rotation matrix embedded in this transformation matrix"""
        return RotationMatrix(
            [
                *self._matrix[0:3],
                *self._matrix[4:7],
                *self._matrix[8:11],
            ]
        )

    def get_translation(self) -> tuple[float, float, float]:
        """Gets the translation embedded in this matrix"""
        return (self._matrix[3], self._matrix[7], self._matrix[11])

    def inverse(self) -> Self:
        """Computes the inverse, outputting a new transformation matrix"""
        rot = self.get_rotation_matrix().inverse()
        trans = self.get_translation()
        return self.from_rotation_matrix_inverse(rot, trans)

    @classmethod
    def from_rotation_matrix(
        cls, matrix: RotationMatrix, translate: tuple[float, float, float]
    ) -> Self:
        """Construct a transformation matrix based on a rotation matrix"""
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
    def from_rotation_matrix_inverse(
        cls, matrix: RotationMatrix, translate: tuple[float, float, float]
    ) -> Self:
        """Construct an inverse transformation based on an inverse rotation matrix"""

        trans_matrix = GenericMatrix(
            (-translate[0], -translate[1], -translate[2]), rows=3, columns=1
        )
        trans_matrix = matrix * trans_matrix
        # fmt: off
        mtx = cls([
            *matrix._matrix[0:3], trans_matrix._matrix[0],
            *matrix._matrix[3:6], trans_matrix._matrix[1],
            *matrix._matrix[6:9], trans_matrix._matrix[2],
            0, 0, 0, 1,
        ])
        # fmt: on
        return mtx
