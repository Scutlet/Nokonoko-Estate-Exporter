import io

from nokonoko_estate.formats.enums import CombinerBlend, WrapMode
from nokonoko_estate.formats.formats import (
    AttrTransform,
    AttributeHeader,
    HSFHeader,
    MaterialObject,
    AttributeObject,
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

        header.bones.offset = self._parse_int()
        header.bones.length = self._parse_int()

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
        name_offset = self._parse_int(signed=True)
        obj = AttributeObject(name_offset)

        obj.tex_animation_offset = self._parse_int(signed=True)
        obj.unk_1 = self._parse_short()
        try:
            obj.blend_flag = CombinerBlend(self._parse_int(0x1, signed=True))
        except ValueError:
            pass
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

        try:
            obj.wrap_s = WrapMode(self._parse_int(signed=True))
        except ValueError:
            pass
        try:
            obj.wrap_t = WrapMode(self._parse_int(signed=True))
        except ValueError:
            pass

        obj.unk_10 = self._parse_int()
        obj.unk_11 = self._parse_int()
        obj.unk_12 = self._parse_int()

        obj.mipmap_max_lod = self._parse_int(signed=True)
        obj.texture_index = self._parse_int(signed=True)

        # print(f"End reading attribute data: {self._fl.tell():#x}")

        return obj


class MaterialObjectParser(HSFParserBase[MaterialObject]):
    """TODO"""

    _data_type = MaterialObject
    struct_formatting = ">lllllliii"


class TextureInfoParser(HSFParserBase[TextureInfo]):
    """TODO"""

    _data_type = TextureInfo
    struct_formatting = ">IIBBHHHIiII"


class PaletteInfoParser(HSFParserBase[PaletteInfo]):
    """TODO"""

    _data_type = PaletteInfo
    struct_formatting = ">IiiI"
