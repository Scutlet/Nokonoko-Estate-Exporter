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

    def __repr__(self):
        return f"HSFTable(offset={self.offset:#x}, length={self.length})"


@dataclass
class HSFFile:
    """HSF File"""

    root_node: "HSFNode" = None
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
    map_attributes: HSFTable = field(default_factory=HSFTable)  # Unused
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
    """
    A single vertex that indices into generic arrays. The index is -1 if unused.
    Indices include position (XYZ-coordinates), vertex normals (XYZ), vertex colors (RGBA), and UV-coordinates

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
    """
    Represents a single face (triangle or quad) or a series of faces (triangle strip). Usually consists of few vertices.

    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    class PrimitiveType(Enum):
        PRIMITIVE_INVALID = 0
        PRIMITIVE_TRIANGLE = 2
        PRIMITIVE_QUAD = 3
        PRIMITIVE_TRIANGLE_STRIP = 4
        PRIMITIVE_FACE_MASK = 7

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
    """
    A helper class for mesh-nodes. Notably consists of a list of primitives (usually single faces)
    whose vertices index into the listed positions, normals, etc.

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
    """Type of node. MESH, REPLICA, and NULL1 are the most common."""

    NULL1 = 0  # Used to group other related nodes together. Can be referenced by REPLICA-nodes to copy all of its children in a different XYZ-location.
    REPLICA = 1  # Copies all children in the HSF tree of the referenced (NULL1) node.
    MESH = 2
    ROOT = 3
    JOINT = 4
    EFFECT = 5
    NULL3 = 6
    CAMERA = 7
    LIGHT = 8
    MAP = 9


# //HSF Object Flags
# define HSF_MATERIAL_BBOARD (1 << 0)
# define HSF_MATERIAL_NOCULL (1 << 1)
# define HSF_MATERIAL_SHADOW (1 << 2)
# define HSF_MATERIAL_SHADOWMAP (1 << 3)
# define HSF_MATERIAL_ADDCOL (1 << 4)
# define HSF_MATERIAL_INVCOL (1 << 5)
# define HSF_MATERIAL_HILITE (1 << 8)
# define HSF_MATERIAL_DISABLE_ZWRITE (1 << 9)
# define HSF_MATERIAL_DISPOFF (1 << 10)
# define HSF_MATERIAL_NEAR (1 << 12)
# define HSF_MATERIAL_MATHOOK (1 << 13)
# define HSF_MATERIAL_REFLECTMODEL (1 << 14)


@dataclass
class NodeTransform:
    """
    Positioning in the world of a node. This transform is relative to its parent
    (or REPLICA-node) in the HSF-tree.

    See: MPLibrary.GCN.Transform
    """

    position: tuple[float, float, float] = field(default_factory=lambda: (0, 0, 0))
    rotation: tuple[float, float, float] = field(default_factory=lambda: (0, 0, 0))
    scale: tuple[float, float, float] = field(default_factory=lambda: (1, 1, 1))


@dataclass
class HSFNode:
    """
    A single node in the HSF-file. Nodes are the core of an HSF-file and together form
    a tree structure. The node tree may not be listed in a DFS or BFS manner in the HSF
    FILE; nodes can appear all-over.
    """

    # Order in which this node appears in the HSF-file. Referenced by REPLICA nodes
    index: int

    # The raw data of a node
    node_data: "HSFNodeData"
    # light_data TODO
    # camera_data TODO

    parent: Optional["HSFNode"] = None
    children: list["HSFNode"] = field(default_factory=list)

    mesh_data: MeshObject = None  # Only set if the node is a MESH node
    replica: Optional["HSFNode"] = None  # Only set if hte node is a REPLICA node
    attribute: "AttributeObject" = None
    # TODO: envelopes, clusters, shapes

    @property
    def has_hierarchy(self):
        """Whether this node can have children"""
        return self.node_data.type not in (HSFNodeType.LIGHT, HSFNodeType.CAMERA)

    def __str__(self):
        parent_name = "<None>"
        replica_name = "<None>"
        if self.parent is not None:
            parent_name = f'HSFObject[{self.parent.node_data.type.name}, "{self.parent.node_data.name}", idx={self.parent.index}]'
        if self.replica is not None:
            replica_name = f'HSFObject[{self.replica.node_data.type.name}, "{self.replica.node_data.name}", idx={self.replica.index}, children={len(self.replica.children)}]'
        return f'HSFNode[{self.node_data.type.name}, "{self.node_data.name}", idx={self.index}, replica={replica_name}, parent={parent_name}, children={len(self.children)}]'

    def dfs(self, visited=None, level=0):
        """Iterate over this node in a depth-first search. Raises a ValueError in case of loops."""
        if visited is None:
            visited: set[HSFNode] = {id(self)}
        yield self, level
        for child in self.children:
            if id(child) not in visited:
                visited.add(id(child))
                yield from child.dfs(visited, level + 1)
            else:
                raise ValueError("Loop encountered in HSF tree structure")


@dataclass
class HSFNodeData(HSFData):
    """
    Raw data for an HSF-node.

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
    current_transform: NodeTransform = field(
        default_factory=NodeTransform
    )  # purpose unknown

    # value below is ONLY used for REPLICA-nodes
    replica_index: int = -1

    # All data below is only used for non-REPLICA nodes
    cull_box_min: tuple[float, float, float] = field(default_factory=lambda: (0, 0, 0))
    cull_box_max: tuple[float, float, float] = field(
        default_factory=lambda: (100, 100, 100)
    )

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


class HSFLightType(Enum):
    """Type of light"""

    SPOT = 0
    POINT = 1
    INFINITE = 2


@dataclass
class HSFNodeDataLight:
    """Node data specific for lights"""

    position: tuple[float, float, float] = field(default_factory=lambda: (0, 0, 0))
    target: tuple[float, float, float] = field(default_factory=lambda: (0, 0, 0))
    light_type: HSFLightType = HSFLightType.SPOT  # byte
    r: int = 0  # byte
    g: int = 0  # byte
    b: int = 0  # byte
    unk2c: float = 0
    ref_distance: float = 0
    ref_brightness: float = 0
    cutoff: float = 0


@dataclass
class HSFNodeDataCamera:
    """Node data specific for cameras"""

    # TODO: first 16 bytes of node data are used as well
    target: tuple[float, float, float] = field(default_factory=lambda: (0, 0, 0))
    position: tuple[float, float, float] = field(default_factory=lambda: (0, 0, 0))
    aspect_ratio: float = 0
    fov: float = 0
    near: float = 0
    far: float = 0


class LightingChannelFlags(Enum):
    NO_LIGHTING = 0  # Flat shading
    LIGHTING = 1  # Lighting used
    LIGHTING_SPECULAR = 2  # Second light channel used for specular
    LIGHTING_SPECULAR_2 = 3  # Same output as LightingSpecular. Not sure if used.
    VERTEX_ALPHA_ONLY = 4  # Vertex colors but only with alpha
    VERTEX_COLORS_WITH_ALPH = 5  # Vertex colors + alpha


@dataclass
class MaterialObject(HSFData):
    """
    Material data referenced by Primitives

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
    attribute_index = -1


@dataclass
class AttrTransform:
    """Transform"""

    scale: tuple[float, float] = field(default_factory=lambda: (1, 1))
    position: tuple[float, float] = field(default_factory=lambda: (0, 0))


@dataclass
class AttributeObject(HSFData):
    """
    Material attributes. Contains alpha state and texture data

    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

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
    nbt_enable: float = 0  # 0 is disabled; 1 is enabled
    unk_3: float = -1
    unk_4: float = 0
    texture_enable: float = 1  # 0 is disabled; 1 is enabled
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
class HSFTextureHeader(HSFData):
    """
    Header data for a texture.

    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    See: https://github.com/KillzXGaming/MPLibrary/blob/master/MPLibrary/GCWii/HSF/Sections/Texture/TextureSection.cs
    """

    name_offset: int  # uint
    max_lod: int  # uint
    tex_format: int  # byte
    bpp: int  # byte; to determine palette types CI4/CI8
    width: int  # ushort
    height: int  # ushort
    palette_entries: int  # ushort
    texture_tint: int  # uint; Used for grayscale (I4, I8) types. Color blends with tev stages as color
    palette_index: int  # -1, usually except for paletted?
    padding: int  # uint; usually 0
    data_offset: int  # uint


@dataclass
class HSFPaletteHeader(HSFData):
    """
    Header data for a palette. Palettes are used by textures.

    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Formats/GameCube/HSF.cs
    """

    name_offset: int  # uint
    format: int
    count: int
    data_offset: int  # uint


@dataclass
class HSFMotionDataHeader(HSFData):
    """
    Motions are used for animations.

    See: MotionDataSection > MotionData in MPLibrary
    """

    string_offset: int  # uint
    track_count: int  # uint
    track_data_offset: int  # uint
    motion_length: float  # Number of frames

    tracks: list["HSFTrackData"] = field(default_factory=list)


class MotionTrackMode(Enum):
    """Type of animation"""

    NORMAL = 2
    OBJECT = 3
    UNKNOWN = 4
    CLUSTER_CURVE = 5
    CLUSTER_WEIGHT_CURVE = 6
    CAMERA = 7
    LIGHT = 8
    MATERIAL = 9
    ATTRIBUTE = 10


class MotionTrackEffect(Enum):
    """
    Animation effects

    See also: https://github.com/mariopartyrd/marioparty5
    """

    AMBIENT_COLOR_R = 0
    AMBIENT_COLOR_G = 1
    AMBIENT_COLOR_B = 2

    TRANSLATE_X = 8
    TRANSLATE_Y = 9
    TRANSLATE_Z = 10

    LIGHT_AIM_X = 11  # or camera target x
    LIGHT_AIM_Y = 12  # or camera target y
    LIGHT_AIM_Z = 13  # or camera target z

    CAMERA_ASPECT = 14
    CAMERA_FOV = 15

    VISIBLE = 24

    ROTATION_X = 28
    ROTATION_Y = 29
    ROTATION_Z = 30
    SCALE_X = 31
    SCALE_Y = 32
    SCALE_Z = 33
    B_TRANSLATE_X = 34
    B_TRANSLATE_Y = 35
    B_TRANSLATE_Z = 36
    B_ROTATION_X = 37
    B_ROTATION_Y = 38
    B_ROTATION_Z = 39
    MORPH_BLEND = 40
    B_SCALE_X = 41
    B_SCALE_Y = 42
    B_SCALE_Z = 43

    MATERIAL_COLOR_R = 49
    MATERIAL_COLOR_G = 50
    MATERIAL_COLOR_B = 51
    SHADOW_COLOR_R = 52
    SHADOW_COLOR_G = 53
    SHADOW_COLOR_B = 54
    HILITE_SCALE = 55
    MAT_UNKNOWN_2 = 56
    TRANSPARENCY = 57
    MAT_UNKNOWN_3 = 58
    MAT_UNKNOWN_4 = 59
    REFLECTION_INTENSITY = 60
    MAT_UNKNOWN_5 = 61
    COMBINER_BLENDING = 62

    UNKNOWN_6 = 63
    UNKNOWN_7 = 64
    UNKNOWN_8 = 65
    UNKNOWN_9 = 66

    TEXTURE_INDEX = 67


class InterpolationMode(Enum):
    """Animation interpolation mode"""

    STEP = 0
    LINEAR = 1
    BEZIER = 2
    BITMAP = 3
    CONSTANT = 4
    ZERO = 5


@dataclass
class HSFTrackData:
    """
    Keyframe data for animations

    See MotionDataSection > TrackData in MPLibrary
    """

    mode: MotionTrackMode  # byte
    unk: int = 0  # byte
    string_offset: int = -1  # short
    value_index: int = -1  # short
    effect: MotionTrackEffect = MotionTrackEffect.AMBIENT_COLOR_B  # short
    interpolate_type: InterpolationMode = InterpolationMode.LINEAR  # short
    keyframe_count: int = 0  # short
    keyframe_offset: int = -1
    constant: float = 0


@dataclass
class KeyFrame:
    """Normal keyframes"""

    frame: float
    value: float


@dataclass
class BezierKeyFrame(KeyFrame):
    """Keyframe for bezier-interpolated animations"""

    slope_in: float
    slope_out: float
