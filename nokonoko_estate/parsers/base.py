import io
import logging
import struct
from typing import Generic, TypeVar

from nokonoko_estate.formats import HSFData, HSFHeader

T = TypeVar("T", bound=HSFData)
T2 = TypeVar("T", bound=HSFData)


class HSFParserBase(Generic[T]):
    """TODO"""

    _data_type: type[T] = HSFData

    def __init__(self, fl: io.BufferedReader, header: HSFHeader | None = None):
        self._fl = fl
        self._header = header

    _byteorder = "big"
    logger = logging.Logger(__name__)

    # See: https://docs.python.org/3/library/struct.html#format-characters
    # NB: No automatic padding is added to the structs!
    struct_formatting: str = ""

    def parse(self) -> T:
        """TODO"""
        if not self.struct_formatting:
            raise NotImplementedError(
                f"{self.__class__.__name__}.struct_formatting was not set. Custom parsing should be implemented."
            )
        return self._data_type(
            *struct.unpack(
                self.struct_formatting,
                self._fl.read(struct.calcsize(self.struct_formatting)),
            )
        )

    def _parse_int(self, size=4) -> int:
        """Parses an int"""
        return int.from_bytes(self._fl.read(size), byteorder=self._byteorder)

    def _parse_short(self) -> int:
        """Parses a short"""
        return self._parse_int(size=2)

    def _parse_float(self, size=4) -> int:
        """Parses a float"""
        return struct.unpack(">f", self._fl.read(size))[0]

    def _parse_string(self, size=-1, format="utf-8"):
        """Parse a (utf-8) string. If `size = -1`, read until a NULL-char"""
        if size < 0:
            string = bytearray()
            while (char := self._fl.read(0x01)) != b"\x00":
                string += char
            return string.decode(format)
        return "METHOD-NOT-IMPLEMENTED"

    def _parse_from_stringtable(self, ofs: int, size=-1, format="utf-8"):
        """Parse a string from a stringtable"""
        assert (
            self._header is not None
        ), "Cannot parse from stringtable without a header"
        prev_pos = self._fl.tell()
        self._fl.seek(self._header.stringtable.offset + ofs, io.SEEK_SET)
        string = self._parse_string(size, format)
        self._fl.seek(prev_pos, io.SEEK_SET)
        return string

    def _parse_array(
        self, parser_cl: type["HSFParserBase[T2]"], count: int
    ) -> list[T2]:
        """TODO"""
        parser = parser_cl(self._fl, self._header)
        data: list[T2] = []
        for _ in range(count):
            data.append(parser.parse())
        return data
