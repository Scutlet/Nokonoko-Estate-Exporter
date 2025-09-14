import io

from nokonoko_estate.formats.enums import CombinerBlend, WrapMode
from nokonoko_estate.formats.formats import (
    AttrTransform,
    AttributeHeader,
    HSFHeader,
    HSFNodeData,
    HSFNodeType,
    LightingChannelFlags,
    MaterialObject,
    AttributeObject,
    NodeTransform,
    PaletteInfo,
    TextureInfo,
    Vertex,
)
from nokonoko_estate.parsers.base import HSFParserBase


class HSFHeaderParser(HSFParserBase[HSFHeader]):
    """Parses a HSFV037 header"""

    _data_type = HSFHeader

    def parse(self) -> HSFHeader:
        magic = self._fl.read(0x08)
        if magic != b"HSFV037\x00":
            self.logger.error("Invalid file magic")
            exit(1)

        header = HSFHeader(magic)

        # Offsets are all relative to the start of the file
        header.fogs.offset = self._parse_int()
        header.fogs.length = self._parse_int()
        header.colors.offset = self._parse_int()
        header.colors.length = self._parse_int()
        header.materials.offset = self._parse_int()
        header.materials.length = self._parse_int()
        header.attributes.offset = self._parse_int()
        header.attributes.length = self._parse_int()

        header.positions.offset = self._parse_int()
        header.positions.length = self._parse_int()

        header.normals.offset = self._parse_int()
        header.normals.length = self._parse_int()

        header.uvs.offset = self._parse_int()
        header.uvs.length = self._parse_int()

        header.primitives.offset = self._parse_int()
        header.primitives.length = self._parse_int()

        # Bones/nodes tie everything together
        header.nodes.offset = self._parse_int()
        header.nodes.length = self._parse_int()

        header.textures.offset = self._parse_int()
        header.textures.length = self._parse_int()

        header.palettes.offset = self._parse_int()
        header.palettes.length = self._parse_int()

        header.motions.offset = self._parse_int()
        header.motions.length = self._parse_int()

        header.rigs.offset = self._parse_int()
        header.rigs.length = self._parse_int()

        header.skeletons.offset = self._parse_int()
        header.skeletons.length = self._parse_int()

        # Unused
        header.parts.offset = self._parse_int()
        header.parts.length = self._parse_int()
        header.clusters.offset = self._parse_int()
        header.clusters.length = self._parse_int()
        header.shapes.offset = self._parse_int()
        header.shapes.length = self._parse_int()
        header.map_attributes.offset = self._parse_int()
        header.map_attributes.length = self._parse_int()
        # end unused

        header.matrices.offset = self._parse_int()
        header.matrices.length = self._parse_int()
        header.symbols.offset = self._parse_int()
        header.symbols.length = self._parse_int()

        header.stringtable.offset = self._parse_int()
        header.stringtable.length = self._parse_int()

        return header


class HSFNodeParser(HSFParserBase[HSFNodeData]):
    """Parses XXX"""

    _data_type = HSFNodeData

    def parse(self) -> HSFNodeData:
        str_ofs = self._parse_int()
        name = self._parse_from_stringtable(str_ofs, -1)

        node_data = HSFNodeData(name)
        node_data.type = HSFNodeType(self._parse_int())
        # print(f"> {name or '<empty>'} ({node_data.type.name})")
        node_data.const_data_ofs = self._parse_int()
        node_data.render_flags = self._parse_int()

        node_data.parent_index = self._parse_index()
        node_data.children_count = self._parse_int()
        node_data.symbol_index = self._parse_index()
        node_data.base_transform = NodeTransform(
            (self._parse_float(), self._parse_float(), self._parse_float()),
            (self._parse_float(), self._parse_float(), self._parse_float()),
            (self._parse_float(), self._parse_float(), self._parse_float()),
        )
        node_data.current_transform = NodeTransform(
            (self._parse_float(), self._parse_float(), self._parse_float()),
            (self._parse_float(), self._parse_float(), self._parse_float()),
            (self._parse_float(), self._parse_float(), self._parse_float()),
        )
        node_data.cull_box_min = (
            self._parse_float(),
            self._parse_float(),
            self._parse_float(),
        )
        node_data.cull_box_max = (
            self._parse_float(),
            self._parse_float(),
            self._parse_float(),
        )
        node_data.base_morph = self._parse_float()
        node_data.morph_weights = self._fl.read(0x20 * 4)

        node_data.unk_index = self._parse_index()
        node_data.primitives_index = self._parse_index()
        node_data.positions_index = self._parse_index()
        node_data.nrm_index = self._parse_index()
        node_data.color_index = self._parse_index()
        # 0xd4
        node_data.uv_index = self._parse_index()

        node_data.material_data_ofs = self._parse_int()
        node_data.attribute_index = self._parse_index()  # Materials
        node_data.unk02 = self._parse_byte()  # byte
        node_data.unk03 = self._parse_byte()  # byte
        node_data.shape_type = self._parse_byte()  # byte
        node_data.unk04 = self._parse_byte()  # byte
        node_data.shape_count = self._parse_int()
        node_data.shape_symbol_index = self._parse_index()
        node_data.cluster_count = self._parse_int()
        node_data.cluster_symbol_index = self._parse_index()
        node_data.cenv_count = self._parse_int()
        node_data.cenv_index = self._parse_index()
        node_data.cluster_position_ofs = self._parse_int()
        node_data.cluster_nrm_ofs = self._parse_int()
        return node_data


class AttributeHeaderParser(HSFParserBase[AttributeHeader]):
    """TODO"""

    _data_type = AttributeHeader
    struct_formatting = ">iii"


class VertexParser(HSFParserBase[Vertex]):
    """TODO"""

    _data_type = Vertex
    struct_formatting = ">hhhh"


class AttributeParser(HSFParserBase[AttributeObject]):
    """TODO"""

    _data_type = AttributeObject

    def parse(self) -> AttributeObject:
        str_ofs = self._parse_index()
        name = None
        if str_ofs != -1:
            name = self._parse_from_stringtable(str_ofs, -1)
        obj = AttributeObject(name)

        obj.tex_animation_offset = self._parse_index()
        obj.unk_1 = self._parse_short()
        obj.blend_flag = CombinerBlend(self._parse_index(0x1))

        obj.alpha_flag = bool(self._parse_int(0x1))
        obj.blend_texture_alpha = self._parse_float()
        obj.unk_2 = self._parse_int()
        obj.nbt_enable = self._parse_float()
        obj.unk_3 = self._parse_float()
        obj.unk_4 = self._parse_float()
        obj.texture_enable = self._parse_float()
        obj.unk_5 = self._parse_float()
        obj.tex_anim_start = AttrTransform(
            (self._parse_float(), self._parse_float()),
            (self._parse_float(), self._parse_float()),
        )
        obj.tex_anim_end = AttrTransform(
            (self._parse_float(), self._parse_float()),
            (self._parse_float(), self._parse_float()),
        )
        obj.unk_6 = self._parse_float()
        obj.rotation = (self._parse_float(), self._parse_float(), self._parse_float())
        obj.unk_7 = self._parse_float()
        obj.unk_8 = self._parse_float()
        obj.unk_9 = self._parse_float()

        obj.wrap_s = WrapMode(self._parse_int(signed=True))
        obj.wrap_t = WrapMode(self._parse_int(signed=True))

        obj.unk_10 = self._parse_int()
        obj.unk_11 = self._parse_int()
        obj.unk_12 = self._parse_int()

        obj.mipmap_max_lod = self._parse_int(signed=True)
        obj.texture_flags = self._parse_int()
        obj.texture_index = self._parse_index()

        return obj


class MaterialObjectParser(HSFParserBase[MaterialObject]):
    """TODO"""

    _data_type = MaterialObject

    def parse(self) -> MaterialObject:
        str_ofs = self._parse_index()
        name = None
        if str_ofs != -1:
            name = self._parse_from_stringtable(str_ofs, -1)
        mat = MaterialObject(name)
        mat.unk01 = self._parse_int()
        mat.alt_flags = self._parse_short()
        mat.vertex_mode = LightingChannelFlags(self._parse_byte())
        mat.ambient_color = (self._parse_byte(), self._parse_byte(), self._parse_byte())
        mat.material_color = (
            self._parse_byte(),
            self._parse_byte(),
            self._parse_byte(),
        )
        mat.shadow_color = (self._parse_byte(), self._parse_byte(), self._parse_byte())
        mat.hi_lite_scale = self._parse_float()
        mat.unk02 = self._parse_float()
        mat.transparency_inverted = self._parse_float()
        mat.unk03 = self._parse_float()
        mat.unk04 = self._parse_float()
        mat.reflection_intensity = self._parse_float()
        mat.unk05 = self._parse_float()
        mat.material_flags = self._parse_int()
        mat.texture_count = self._parse_int()
        mat.attribute_index = self._parse_int()

        return mat


class TextureInfoParser(HSFParserBase[TextureInfo]):
    """TODO"""

    _data_type = TextureInfo
    struct_formatting = ">IIBBHHHIiII"


class PaletteInfoParser(HSFParserBase[PaletteInfo]):
    """TODO"""

    _data_type = PaletteInfo
    struct_formatting = ">IiiI"
