from dataclasses import dataclass, field
from enum import Enum
from io import BufferedReader
import struct
from typing import ClassVar, Generic, Optional, Self, TypeVar

from PIL import Image

from nokonoko_estate.formats.enums import CombinerBlend, WrapMode

# See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs


class HSFData:
    """Any HSF-related data"""


@dataclass
class HSFTable:
    """
    `offset` is relative to the start of the HSF file. `size` in number of items.
    If `offset` is zero, then the data is absent
    """

    offset: int = 0
    length: int = 0


@dataclass
class HSFFile:
    """HSF File"""

    nodes: list["HSFNode"] = field(default_factory=list)
    textures: list[tuple[str, Image.Image]] = field(default_factory=list)
    materials: list["MaterialObject"] = field(default_factory=list)
    attributes: list["AttributeObject"] = field(default_factory=list)


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
    nodes: HSFTable = field(default_factory=HSFTable)
    textures: HSFTable = field(default_factory=HSFTable)
    palettes: HSFTable = field(default_factory=HSFTable)
    motions: HSFTable = field(default_factory=HSFTable)
    rigs: HSFTable = field(default_factory=HSFTable)  # cenv
    skeletons: HSFTable = field(default_factory=HSFTable)

    # Unused data
    parts: HSFTable = field(default_factory=HSFTable)
    clusters: HSFTable = field(default_factory=HSFTable)
    shapes: HSFTable = field(default_factory=HSFTable)
    map_attributes: HSFTable = field(default_factory=HSFTable)
    # end

    matrices: HSFTable = field(default_factory=HSFTable)
    symbols: HSFTable = field(default_factory=HSFTable)
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
T = TypeVar("T", bound=HSFData)


@dataclass
class HSFAttributes(Generic[T]):
    """
    A named list of HSF attributes
    """

    name: str
    data: list[T] = field(default_factory=list)


@dataclass
class PrimitiveObject(HSFData):
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    class PrimitiveType(Enum):
        PRIMITIVE_TRIANGLE = 2
        PRIMITIVE_QUAD = 3
        PRIMITIVE_TRIANGLE_STRIP = 4

    primitive_type: PrimitiveType
    flags: int = 0
    vertices: list[Vertex] = field(default_factory=list)
    tri_count: int = 0  # only used for triangle strips
    nbt_data: tuple[int, int, int] = field(default_factory=lambda: (0, 0, 0))

    # Calculated based on flags
    material_index: int = -1
    flag_value: int = 8

    def __str__(self):
        return f"PrimitiveObject[{self.primitive_type.name}, vertices={len(self.vertices)}, mat={self.material_index}, tris={self.tri_count}]"


@dataclass
class MeshObject(HSFData):
    """TODO
    This is a placeholder class that ties everything together
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    name: str
    single_bind: int = -1
    positions: list[tuple[int, int, int]] = field(default_factory=list)
    normals: list[tuple[int, int, int]] = field(default_factory=list)
    uvs: list[tuple[int, int]] = field(default_factory=list)
    colors: list[tuple[int, int, int, int]] = field(default_factory=list)

    # Triangles, quads, etc.
    primitives: list[PrimitiveObject] = field(default_factory=list)

    single_binds: list[RiggingSingleBind] = field(default_factory=list)
    rigging_double_binds: list[RiggingDoubleBind] = field(default_factory=list)
    multi_binds: list[RiggingMultiBind] = field(default_factory=list)
    double_weights: list[RiggingDoubleWeight] = field(default_factory=list)
    multi_weights: list[RiggingMultiWeight] = field(default_factory=list)

    def __str__(self):
        return f'MeshObject["{self.name}", primitives={len(self.primitives)}, positions={len(self.positions)}, normals={len(self.normals)}, uvs={len(self.uvs)}, colors={len(self.colors)}]'


class HSFNodeType(Enum):
    """Type of object"""

    NULL1 = 0
    REPLICA = 1
    MESH = 2
    ROOT = 3
    JOINT = 4
    EFFECT = 5
    CAMERA = 7
    LIGHT = 8
    MAP = 9


@dataclass
class NodeTransform:
    """TODO
    See: MPLibrary.GCN.Transform
    """

    position: tuple[float, float, float] = field(default_factory=lambda: (0, 0, 0))
    rotation: tuple[float, float, float] = field(default_factory=lambda: (0, 0, 0))
    scale: tuple[float, float, float] = field(default_factory=lambda: (1, 1, 1))


@dataclass
class HSFNode:
    """TODO"""

    node_data: "HSFNodeData"
    # light_data TODO
    # camera_data TODO

    parent: Optional["HSFNode"] = None
    children: list["HSFNode"] = field(default_factory=list)

    mesh_data: MeshObject = None  # If HSFNodeData.type == MESH
    attribute: "AttributeObject" = None
    # TODO: envelopes, clusters, shapes

    @property
    def has_hierarchy(self):
        """Whether this node can have children"""
        return self.node_data.type not in (HSFNodeType.LIGHT, HSFNodeType.CAMERA)

    def __str__(self):
        parent_name = "<None>"
        if self.parent is not None:
            parent_name = f'HSFObject[{self.parent.node_data.type.name}, "{self.parent.node_data.name}"]'
        return f'HSFNode[{self.node_data.type.name}, "{self.node_data.name}", parent={parent_name}, children={len(self.children)}]'


@dataclass
class HSFNodeData(HSFData):
    """TODO
    See (NodeObject): https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    See: MPLibrary.GCN.HSFObject
    """

    name: str
    type: HSFNodeType = HSFNodeType.NULL1
    const_data_ofs: int = -1
    render_flags: int = 0

    # TODO: Camera data/light data. MPLibrary.GCN.HSFObject.Read
    # TODO: Stuff below isn't used for Camera/lights
    parent_index: int = -1
    children_count: int = 0
    symbol_index: int = -1

    base_transform: NodeTransform = field(default_factory=NodeTransform)
    current_transform: NodeTransform = field(default_factory=NodeTransform)

    cull_box_min: tuple[float, float, float] = field(default_factory=lambda: (1, 1, 1))
    cull_box_max: tuple[float, float, float] = field(default_factory=lambda: (1, 1, 1))

    # fmt: off
    base_morph: float = 0.0
    morph_weights: tuple[float, float, float, float, float, float, float, float,
                         float, float, float, float, float, float, float, float,
                         float, float, float, float, float, float, float, float,
                         float, float, float, float, float, float, float, float] = (
        field(default_factory=lambda: tuple(0.0 for _ in range(0x20)))
    )
    # fmt: on

    unk_index: int = -1
    primitives_index: int = -1  # Faces
    positions_index: int = -1  # Vertices
    nrm_index: int = -1
    color_index: int = -1
    uv_index: int = -1
    material_data_ofs: int = 0  # Set at runtime
    attribute_index: int = -1  # Materials
    unk02: int = 0  # byte
    unk03: int = 0  # byte
    shape_type: int = 0  # byte
    unk04: int = 0  # byte
    shape_count: int = 0
    shape_symbol_index: int = -1
    cluster_count: int = 0
    cluster_symbol_index: int = -1
    cenv_count: int = 0
    cenv_index: int = -1
    cluster_position_ofs: int = 0
    cluster_nrm_ofs: int = 0


class LightingChannelFlags(Enum):
    NO_LIGHTING = 0  # Flat shading
    LIGHTING = 1  # Lighting used
    LIGHTING_SPECULAR = 2  # Second light channel used for specular
    LIGHTING_SPECULAR_2 = 3  # Same output as LightingSpecular. Not sure if used.
    VERTEX_ALPHA_ONLY = 4  # Vertex colors but only with alpha
    VERTEX_COLORS_WITH_ALPH = 5  # Vertex colors + alpha


@dataclass
class MaterialObject(HSFData):  # struct
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    name: str
    unk01: int = 0
    alt_flags: int = 0
    vertex_mode: LightingChannelFlags = LightingChannelFlags.NO_LIGHTING
    ambient_color: tuple[int, int, int] = field(default_factory=lambda: (0, 0, 0))
    material_color: tuple[int, int, int] = field(default_factory=lambda: (0, 0, 0))
    shadow_color: tuple[int, int, int] = field(default_factory=lambda: (0, 0, 0))
    hi_lite_scale: float = 1.0
    unk02: float = 0.0
    transparency_inverted: float = 0.0
    unk03: float = 0.0
    unk04: float = 0.0
    reflection_intensity: float = 1.0
    unk05: float = 1.0
    material_flags: int = 0
    texture_count = 0
    first_symbol = 0


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
    name: str | None
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
    texture_flags: int = 0
    texture_index: int = -1

    def __str__(self):
        return f"AttributeObject[{self.name}, texture={self.texture_index}]"


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
