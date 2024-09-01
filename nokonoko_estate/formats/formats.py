from dataclasses import dataclass, field
from enum import Enum
from io import BufferedReader
import struct
from typing import ClassVar, Self

from PIL import Image

from nokonoko_estate.formats.enums import CombinerBlend, WrapMode

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
    textures: list[tuple[str, Image.Image]] = field(default_factory=list)
    bones: list["BoneObject"] = field(default_factory=list)
    materials_1: list["MaaterialObject"] = field(default_factory=list)
    materials: list["AttributeObject"] = field(default_factory=list)


@dataclass
class HSFHeader:
    """HSF Header"""

    magic: str
    fogs: HSFTable = field(default_factory=HSFTable)
    colors: HSFTable = field(default_factory=HSFTable)
    materials: HSFTable = field(default_factory=HSFTable)
    attributes: HSFTable = field(default_factory=HSFTable)
    positions: HSFTable = field(default_factory=HSFTable)
    normals: HSFTable = field(default_factory=HSFTable)
    uvs: HSFTable = field(default_factory=HSFTable)
    primitives: HSFTable = field(default_factory=HSFTable)
    bones: HSFTable = field(default_factory=HSFTable)
    textures: HSFTable = field(default_factory=HSFTable)
    palettes: HSFTable = field(default_factory=HSFTable)
    motions: HSFTable = field(default_factory=HSFTable)
    rigs: HSFTable = field(default_factory=HSFTable)
    skeletons: HSFTable = field(default_factory=HSFTable)

    # Unused data
    parts: HSFTable = field(default_factory=HSFTable)
    clusters: HSFTable = field(default_factory=HSFTable)
    shapes: HSFTable = field(default_factory=HSFTable)
    map_attributes: HSFTable = field(default_factory=HSFTable)
    # end

    stringtable: HSFTable = field(default_factory=HSFTable)
    matrices: HSFTable = field(default_factory=HSFTable)
    symbols: HSFTable = field(default_factory=HSFTable)


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
class AttrTransform:
    """TODO"""

    scale: tuple[float, float] = field(default_factory=lambda: (1, 1))
    position: tuple[float, float] = field(default_factory=lambda: (0, 0))


@dataclass
class AttributeObject(HSFData):
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    name_offset: int  # uint
    tex_animation_offset: int = (
        0  # Replaced with Pointer to Texture Animation at Runtime
    )
    unk_1: int = 0  # ushort
    blend_flag: CombinerBlend = CombinerBlend.ADDITIVE  # byte
    alpha_flag: bool = False  # Alpha textures use 1 else 0
    blend_texture_alpha: float = (
        1  # Blend with texture alpha else use register color 2 from alpha output
    )
    unk_2: int = 1
    nbt_enable: float = 0  # 0 is diabled; 1 is enabled
    unk_3: float = -1
    unk_4: float = 0
    texture_enable: float = 1  # 0 is diabled; 1 is enabled
    unk_5: float = 0
    tex_anim_start: AttrTransform = field(default_factory=AttrTransform)
    tex_anim_end: AttrTransform = field(default_factory=AttrTransform)
    unk_6: float = 0
    rotation: tuple[float, float, float] = field(default_factory=lambda: (0, 0, 0))

    unk_7: float = 1.0
    unk_8: float = 1.0
    unk_9: float = 1.0

    wrap_s: WrapMode = WrapMode.REPEAT
    wrap_t: WrapMode = WrapMode.REPEAT

    unk_10: int = 1
    unk_11: int = 79
    unk_12: int = 0

    mipmap_max_lod: int = 1
    texture_index: int = -1


@dataclass
class MaaterialObject(HSFData):  # struct
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
    See: https://github.com/KillzXGaming/MPLibrary/blob/master/MPLibrary/GCWii/HSF/Sections/Texture/TextureSection.cs
    """

    name_offset: int  # uint
    max_lod: int  # uint
    tex_format: int  # byte
    bpp: int  # byte; to determine pallete types CI4/CI8
    width: int  # ushort
    height: int  # ushort
    palette_entries: int  # ushort
    texture_tint: int  # uint; Used for grayscale (I4, I8) types. Color blends with tev stages as color
    palette_index: int  # -1, usually except for paletted?
    padding: int  # uint; usually 0
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
