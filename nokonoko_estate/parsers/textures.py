from dataclasses import dataclass
from io import SEEK_CUR, BytesIO
from typing import Callable, Self
from nokonoko_estate.formats.enums import GCNPaletteFormat, GCNTextureFormat

from PIL import Image


def round_up_to_multiple(value: int, multiple: int):
    """
    Rounds `value` up to the nearest multiple of `multiple`

    See: https://github.com/TheShadowEevee/libWiiSharp/blob/master/Shared.cs
    """
    if value % multiple != 0:
        value += multiple - value % multiple
    return value


def get_texture_byte_size(format: GCNTextureFormat, width: int, height: int) -> int:
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Tools/TLP.cs
    """
    match format:
        case GCNTextureFormat.I4:
            return round_up_to_multiple(width, 8) * round_up_to_multiple(height, 8) // 2
        case GCNTextureFormat.I8 | GCNTextureFormat.IA4:
            return round_up_to_multiple(width, 8) * round_up_to_multiple(height, 4)
        case GCNTextureFormat.IA8 | GCNTextureFormat.RGB565 | GCNTextureFormat.RGB5A3:
            return round_up_to_multiple(width, 4) * round_up_to_multiple(height, 4) * 2
        case GCNTextureFormat.RGBA32:
            return round_up_to_multiple(width, 4) * round_up_to_multiple(height, 4) * 4
        case GCNTextureFormat.C4:
            return round_up_to_multiple(width, 8) * round_up_to_multiple(height, 8) // 2
        case GCNTextureFormat.C8:
            return round_up_to_multiple(width, 8) * round_up_to_multiple(height, 4)
        case GCNTextureFormat.C14X2:
            return round_up_to_multiple(width, 4) * round_up_to_multiple(height, 4) * 2
        case GCNTextureFormat.CMPR:
            return round_up_to_multiple(width, 8) * round_up_to_multiple(height, 8) // 2
        case _:
            raise NotImplementedError(f"Invalid GCNTextureFormat {format}")


class BitMapImage:
    """TODO"""

    @classmethod
    def convert_from_texture(
        cls,
        data: bytes,
        width: int,
        height: int,
        format: GCNTextureFormat,
        palette_data: bytes,
        palette_format: GCNPaletteFormat | None,
    ) -> Image.Image:
        """TODO"""
        img = TPLImage()
        rgba: list[int] = []

        if palette_format is not None:
            # Parse Palette
            print(f"Palette format {palette_format.name}")
            pallete_pixels = img.palette_to_rgba(palette_data, palette_format)

        match format:
            case GCNTextureFormat.I4:
                raise NotImplementedError("I4 not implemented")
            case GCNTextureFormat.I8:
                rgba = img.from_i8(data, width, height)
            case GCNTextureFormat.IA4:
                raise NotImplementedError("IA4 not implemented")
            case GCNTextureFormat.IA8:
                raise NotImplementedError("IA8 not implemented")
            case GCNTextureFormat.RGB565:
                rgba = img.from_rgb565(data, width, height)
            case GCNTextureFormat.RGB5A3:
                rgba = img.from_rgb5a3(data, width, height)
            case GCNTextureFormat.RGBA32:
                raise NotImplementedError("RGBA32 not implemented")
            case GCNTextureFormat.C4:
                rgba = img.from_c4(data, width, height, pallete_pixels)
            case GCNTextureFormat.C8:
                rgba = img.from_c8(data, width, height, pallete_pixels)
            case GCNTextureFormat.CMPR:
                rgba = img.from_cmpr(data, width, height)
            case _:
                raise NotImplementedError(f"Cannot decode texture format {format}")
        return img.rgba_to_image(rgba, width, height)


class TPLImage:
    """
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Tools/TLP.cs
    """

    def _average_rgb565_colors(self, c0: int, c1: int, weight_0=1, weight_1=1) -> int:
        """Computes a new RGB565-color by averaging each RGB565-color component according to:
        `(c0 * weight_0 + c1 * weight_1) / (weight_0 + weight_1)`
        """
        # Average R
        r0 = c0 >> 11 & 0x1F
        r1 = c1 >> 11 & 0x1F
        cr = (weight_0 * r0 + weight_1 * r1) // (weight_0 + weight_1)
        # print(r0, r1, cr, cr & 0xFFFF)

        # Average G
        g0 = c0 >> 5 & 0x3F
        g1 = c1 >> 5 & 0x3F
        cg = (weight_0 * g0 + weight_1 * g1) // (weight_0 + weight_1)
        # print(f"({weight_0} * {g0} + {weight_1} * {g1}) // ({weight_0 + weight_1})")
        # print(g0, g1, cg * 0x4, cg & 0xFFFF)
        # print(weight_0, weight_1)
        # exit(0)

        # Average B
        b0 = c0 >> 0 & 0x1F
        b1 = c1 >> 0 & 0x1F
        cb = (weight_0 * b0 + weight_1 * b1) // (weight_0 + weight_1)
        # print(b0, b1, cb, cb & 0xFFFF)
        return cr << 11 | cg << 5 | cb << 0

    def _from_gcn_encoding(
        self,
        data: bytes,
        pixel_fn: Callable[[int, list[int]], int],
        size: tuple[int, int],
        bpp: int,
        block_size: tuple[int, int],
        palette: list[int] | None = None,
    ) -> list[int]:
        """TODO"""
        assert (
            bpp % 8 == 0 or bpp == 4
        ), f"BPP ({bpp}) was not a multiple of 8 (not a multiple of a byte) nor 4 (a nibble)"
        width, height = size
        block_width, block_height = block_size
        output_pixels: list[int] = [None] * (width * height)
        pixel_data = BytesIO(data)

        # i = 0

        for block_y in range(0, (height - 1) // block_height + 1):
            for block_x in range(0, (width - 1) // block_width + 1):
                for y in range(block_height):
                    if block_y * block_height + y > height:
                        continue
                    for x in range(block_width):
                        if block_x * block_width + x > width:
                            continue
                        if bpp == 4:
                            # Special handling when reading nibbles
                            pixel = int.from_bytes(pixel_data.read(1), byteorder="big")
                            if x % 2 == 0:
                                pixel_data.seek(-1, SEEK_CUR)
                                pixel = pixel >> 4
                            else:
                                pixel = pixel & 0x0F
                        else:
                            pixel = int.from_bytes(
                                pixel_data.read(bpp // 8), byteorder="big"
                            )
                        index = (
                            width * y
                            + x
                            + block_x * block_width
                            + block_y * (width * block_height)
                        )
                        output_pixels[index] = pixel_fn(pixel, palette)
                        # if i > 8:
                        #     break
                        # i += 1
                        # print(
                        #     f"index={index}\ti={i}, block_x={block_x}, block_y={block_y}, x={x}, y={y}"
                        # )
        return output_pixels

    def palette_to_rgba(self, data: bytes, palette_format: GCNPaletteFormat):
        """TODO"""
        palette_data = BytesIO(data)
        format_fn: Callable[[int], int] = None
        match palette_format:
            case GCNPaletteFormat.IA8:
                format_fn = None
                raise NotImplementedError("IA8 decoding not yet implemented")
            case GCNPaletteFormat.RGB565:
                format_fn = self._rgb565_to_rgba
            case GCNPaletteFormat.RGB5A3:
                format_fn = self._rgb5a3_to_rgba
            case _:
                raise NotImplementedError(
                    f"Palette format {palette_format} is unsupported"
                )
        palette: list[int] = []
        for _ in range(len(data) // 2):
            pixel = int.from_bytes(palette_data.read(0x02), byteorder="big")
            palette.append(format_fn(pixel, []))
        return palette

    def _i8_to_rgba(self, pixel: int, palette: list[int]) -> int:
        """Parses an int as an I8-pixel and outputs an int representing an RGBA-pixel"""
        return pixel << 24 | pixel << 16 | pixel << 8 | 0xFF << 0

    def from_i8(self, data: bytes, width: int, height: int) -> list[int]:
        """TODO"""
        return self._from_gcn_encoding(
            data, self._i8_to_rgba, (width, height), 8, (8, 4)
        )

    def _rgb5a3_to_rgba(self, pixel: int, palette: list[int]) -> int:
        """Parses an int as an RGB5A3-pixel and outputs an int representing an RGBA-pixel"""
        if pixel >> 15 & 1:
            # No alpha component
            a = 0xFF
            r = (pixel >> 10 & 0x1F) * 255 // 0x1F
            g = (pixel >> 5 & 0x1F) * 255 // 0x1F
            b = (pixel >> 0 & 0x1F) * 255 // 0x1F
        else:
            # Alpha component
            # if pixel & 0b1111000000000000:
            #     print(pixel)
            #     exit(0)
            a = (pixel >> 12 & 0x07) * 255 // 0x07
            r = (pixel >> 8 & 0x0F) * 255 // 0x0F
            g = (pixel >> 4 & 0x0F) * 255 // 0x0F
            b = (pixel >> 0 & 0x0F) * 255 // 0x0F
        return r << 24 | g << 16 | b << 8 | a << 0

    def from_rgb5a3(self, data: bytes, width: int, height: int) -> list[int]:
        """TODO"""
        return self._from_gcn_encoding(
            data, self._rgb5a3_to_rgba, (width, height), 16, (4, 4)
        )

    def _rgb565_to_rgba(self, pixel: int, palette: list[int]) -> int:
        """Parses an int as an RGB565-pixel and outputs an int representing an RGBA-pixel"""
        # No alpha component
        a = 0xFF
        r = (pixel >> 11 & 0x1F) * 255 // 0x1F
        g = (pixel >> 5 & 0x3F) * 255 // 0x3F
        b = (pixel >> 0 & 0x1F) * 255 // 0x1F
        # print(f"RGBA: {r}-{g}-{b}-{a}")
        return r << 24 | g << 16 | b << 8 | a << 0

    def from_rgb565(self, data: bytes, width: int, height: int) -> list[int]:
        """TODO"""

        return self._from_gcn_encoding(
            data, self._rgb565_to_rgba, (width, height), 16, (4, 4)
        )

    def _palette_to_rgba(self, pixel: int, palette: list[int]) -> int:
        """Parses an int as a palette-pixel and outputs an int representing an RGBA-pixel"""
        assert len(palette) > pixel
        return palette[pixel]

    def from_c4(
        self, data: bytes, width: int, height: int, palette: list[int]
    ) -> list[int]:
        """TODO"""
        return self._from_gcn_encoding(
            data, self._palette_to_rgba, (width, height), 4, (8, 8), palette
        )

    def from_c8(
        self, data: bytes, width: int, height: int, palette: list[int]
    ) -> list[int]:
        """TODO"""
        return self._from_gcn_encoding(
            data, self._palette_to_rgba, (width, height), 8, (8, 4), palette
        )

    def from_cmpr(self, data: bytes, width: int, height: int) -> list[int]:
        """TODO"""
        output_pixels: list[int] = [0] * (width * height)
        img_data = BytesIO(data)
        # Block size is 8*8

        for block_y in range(0, (height - 1) // 8 + 1):
            for block_x in range(0, (width - 1) // 8 + 1):
                # Each block contains 2x2 sub-blocks
                for subblock_y in range(2):
                    for subblock_x in range(2):
                        palette = []
                        # Each sub-block has its own palette, utilising DXT1/BC1-compression
                        c0 = int.from_bytes(img_data.read(0x02), byteorder="big")
                        c1 = int.from_bytes(img_data.read(0x02), byteorder="big")

                        if c0 > c1:
                            c2 = self._average_rgb565_colors(c0, c1, 2, 1)
                            c3 = self._average_rgb565_colors(c0, c1, 1, 2)
                            c3 = self._rgb565_to_rgba(c3, None)
                        else:
                            c2 = self._average_rgb565_colors(c0, c1, 1, 1)
                            c3 = 0x00

                        palette.append(self._rgb565_to_rgba(c0, None))
                        palette.append(self._rgb565_to_rgba(c1, None))
                        palette.append(self._rgb565_to_rgba(c2, None))
                        palette.append(c3)

                        # Each byte represents a row in the sub-block
                        for row in range(4):
                            rowdata = int.from_bytes(
                                img_data.read(0x01), byteorder="big"
                            )
                            for col in range(4):
                                # Pixels in each sub-block are organised LTR, TTB
                                #   All blocks are laid out LTR, TTB
                                palette_index = rowdata >> ((3 - col) * 2) & 0b11
                                img_x = col + subblock_x * 4 + block_x * 8
                                img_y = row + subblock_y * 4 + block_y * 8
                                index = img_x + width * img_y

                                output_pixels[index] = palette[palette_index]
        return output_pixels

    def rgba_to_image(self, rgba: list[int], width: int, height: int) -> Image.Image:
        """TODO"""

        img = Image.frombytes(
            "RGBA",
            (width, height),
            b"".join([int.to_bytes(pixel, 4) for pixel in rgba]),
        )
        return img
