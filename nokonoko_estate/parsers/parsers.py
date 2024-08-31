import io

from nokonoko_estate.formats.formats import (
    AttributeHeader,
    HSFHeader,
    Material1Object,
    MaterialObject,
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

        header.size = self._parse_int()
        print(f"Header size: {header.size:#x}")

        # unk
        self._fl.seek(0x08, io.SEEK_CUR)

        header.flag = self._parse_int()
        # Offsets are all relative to the start of the file
        header.material_1s.offset = self._parse_int()
        header.material_1s.length = self._parse_int()
        header.materials.offset = self._parse_int()
        header.materials.length = self._parse_int()

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

        header.texture.offset = self._parse_int()
        header.texture.length = self._parse_int()

        header.palette.offset = self._parse_int()
        header.palette.length = self._parse_int()

        # unk
        self._fl.seek(0x04, io.SEEK_CUR)
        self._fl.seek(0x04, io.SEEK_CUR)

        header.rig.offset = self._parse_int()
        header.rig.length = self._parse_int()

        # unk
        self._fl.seek(0x38, io.SEEK_CUR)

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


class MaterialObjectParser(HSFParserBase[MaterialObject]):
    """TODO"""

    _data_type = MaterialObject
    struct_formatting = ">lllllllllllllllli"


class Material1ObjectParser(HSFParserBase[Material1Object]):
    """TODO"""

    _data_type = Material1Object
    struct_formatting = ">lllllliii"


class TextureInfoParser(HSFParserBase[TextureInfo]):
    """TODO"""

    _data_type = TextureInfo
    struct_formatting = ">IIBBHHHIiII"


class PaletteInfoParser(HSFParserBase[PaletteInfo]):
    """TODO"""

    _data_type = PaletteInfo
    struct_formatting = ">IiiI"
