from dataclasses import dataclass, field
from enum import Enum
from io import BufferedReader
import struct
from typing import ClassVar, Self

# See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs


class HSFData:
    """Any HSF-related data"""


@dataclass
class HSFTable:
    """`offset` is relative to the start of the HSF file. `size` in number of items."""

    offset: int = -1
    length: int = 0


@dataclass
class HSFFile:
    """HSF File"""

    mesh_objects: dict[str, "MeshObject"] = field(default_factory=dict)
    textures: list = field(default_factory=list)  # GenericTexture
    bones: list["BoneObject"] = field(default_factory=list)
    materials_1: list["Material1Object"] = field(default_factory=list)
    materials: list["MaterialObject"] = field(default_factory=list)


@dataclass
class HSFHeader:
    """HSF Header"""

    magic: str
    size: int = -1
    flag: int = -1
    material_1s: HSFTable = field(default_factory=HSFTable)
    materials: HSFTable = field(default_factory=HSFTable)
    positions: HSFTable = field(default_factory=HSFTable)
    normals: HSFTable = field(default_factory=HSFTable)
    uvs: HSFTable = field(default_factory=HSFTable)
    primitives: HSFTable = field(default_factory=HSFTable)
    bones: HSFTable = field(default_factory=HSFTable)
    texture: HSFTable = field(default_factory=HSFTable)
    palette: HSFTable = field(default_factory=HSFTable)
    rig: HSFTable = field(default_factory=HSFTable)
    stringtable: HSFTable = field(default_factory=HSFTable)


@dataclass
class AttributeHeader(HSFData):
    """

    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    string_offset: int
    data_count: int
    data_offset: int


@dataclass
class Vertex(HSFData):
    """TODO

    See (VertexGroup): https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    position_index: int  # short
    normal_index: int  # short
    color_index: int  # short
    uv_index: int  # short


@dataclass
class RiggingSingleBind(HSFData):
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    bone_index: int
    position_index: int  # short
    position_count: int  # short
    normal_index: int  # short
    normal_count: int  # short


@dataclass
class RiggingDoubleBind(HSFData):
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    bone_1: int
    bone_2: int
    count: int
    weight_offset: int


@dataclass
class RiggingMultiBind(HSFData):
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    count: int
    position_index: int  # short
    position_count: int  # short
    normal_index: int  # short
    normal_count: int  # short
    weight_offset: int


@dataclass
class RiggingDoubleWeight(HSFData):
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    weight: float
    position_index: int  # short
    position_count: int  # short
    normal_index: int  # short
    normal_count: int  # short


@dataclass
class RiggingMultiWeight(HSFData):
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    bone_index: int
    weight: float


################


@dataclass
class PrimitiveObject(HSFData):
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    class PrimitiveType(Enum):
        PRIMITIVE_0 = 0
        PRIMITIVE_1 = 1
        PRIMITIVE_TRIANGLE = 2
        PRIMITIVE_QUAD = 3
        PRIMITIVE_TRIANGLE_STRIP = 4

    primitive_type: PrimitiveType
    material: int
    vertices: list[Vertex] = field(default_factory=list)
    unk: list[tuple[int, int, int]] = field(default_factory=list)
    tri_count: int = 0


@dataclass
class MeshObject(HSFData):
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    name: str
    single_bind: int = -1
    positions: list[tuple[int, int, int]] = field(default_factory=list)
    normals: list[tuple[int, int, int]] = field(default_factory=list)
    uvs: list[tuple[int, int]] = field(default_factory=list)
    colors: list[tuple[int, int, int, int]] = field(default_factory=list)

    primitives: list[PrimitiveObject] = field(default_factory=list)
    single_binds: list[RiggingSingleBind] = field(default_factory=list)
    rigging_double_binds: list[RiggingDoubleBind] = field(default_factory=list)
    multi_binds: list[RiggingMultiBind] = field(default_factory=list)
    double_weights: list[RiggingDoubleWeight] = field(default_factory=list)
    multi_weights: list[RiggingMultiWeight] = field(default_factory=list)


@dataclass
class BoneObject(HSFData):
    """TODO
    See (NodeObject): https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    name: str
    parent_index: int = -1
    type: int = 0
    material_index: int = 0
    position: tuple[float, float, float] = field(default_factory=lambda: (1, 1, 1))
    rotation: tuple[float, float, float] = field(default_factory=lambda: (1, 1, 1))
    scale: tuple[float, float, float] = field(default_factory=lambda: (1, 1, 1))


@dataclass
class MaterialObject(HSFData):  # struct
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    unk_1: int  # long
    unk_2: int  # long
    unk_3: int  # long
    unk_4: int  # long
    unk_5: int  # long
    unk_6: int  # long
    unk_7: int  # long
    unk_8: int  # long
    unk_9: int  # long
    unk_10: int  # long
    unk_11: int  # long
    unk_12: int  # long
    unk_13: int  # long
    unk_14: int  # long
    unk_15: int  # long
    unk_16: int  # long
    texture_index: int


@dataclass
class Material1Object(HSFData):  # struct
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    unk_1: int  # long
    unk_2: int  # long
    unk_3: int  # long
    unk_4: int  # long
    unk_5: int  # long
    unk_6: int  # long
    unk_7: int
    material_count: int
    material_index: int


##############
# TEXTURE
##############
@dataclass
class TextureInfo(HSFData):
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    name_offset: int  # uint
    padding: int  # uint
    type_1: int  # byte
    type_2: int  # byte
    width: int  # ushort
    height: int  # ushort
    depth: int  # ushort
    padding_1: int  # uint; usually 0
    palette_index: int  # -1, usually except for paletted?
    padding_3: int  # uint; usually 0
    data_offset: int  # uint


@dataclass
class PaletteInfo(HSFData):
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    name_offset: int  # uint
    format: int
    count: int
    data_offset: int  # uint
