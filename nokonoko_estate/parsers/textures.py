from dataclasses import dataclass
from io import BytesIO
from typing import Self
from nokonoko_estate.formats.enums import GCNPaletteFormats, GCNTextureFormats

from PIL import Image


def add_padding(value: int, padding: int):
    """TODO
    See: https://github.com/TheShadowEevee/libWiiSharp/blob/master/Shared.cs
    """
    if value % padding != 0:
        value += padding - value % padding
    return value


def get_texture_byte_size(format: GCNTextureFormats, width: int, height: int) -> int:
    """TODO
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Tools/TLP.cs
    """
    match format:
        case GCNTextureFormats.I4:
            return add_padding(width, 8) * add_padding(height, 8) / 2
        case GCNTextureFormats.I8 | GCNTextureFormats.IA4:
            return add_padding(width, 8) * add_padding(height, 4)
        case (
            GCNTextureFormats.IA8 | GCNTextureFormats.RGB565 | GCNTextureFormats.RGB5A3
        ):
            return add_padding(width, 4) * add_padding(height, 4) * 2
        case GCNTextureFormats.RGBA32:
            return add_padding(width, 4) * add_padding(height, 4) * 4
        case GCNTextureFormats.C4:
            return add_padding(width, 8) * add_padding(height, 8) / 2
        case GCNTextureFormats.C8:
            return add_padding(width, 8) * add_padding(height, 4)
        case GCNTextureFormats.C14X2:
            return add_padding(width, 4) * add_padding(height, 4) * 2
        case GCNTextureFormats.CMPR:
            return add_padding(width, 8) * add_padding(height, 8) / 2
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
        format: GCNTextureFormats,
        palette_data: bytes,
        palette_count: int,
        palette_format: GCNPaletteFormats,
    ) -> Self:
        """TODO"""
        img = TPLImage()
        pal_rgba: list[int] = []
        rgba: bytes = None

        # if palette_data:
        #     # print(palette_data)
        #     header = TPLImage.PaletteHeader(palette_count, palette_format=format)
        #     pal_rgba = img.palette_to_rgba(header, palette_data)
        #     print(pal_rgba)

        match format:
            case GCNTextureFormats.I4:
                raise NotImplementedError("I4 not implemented")
            case GCNTextureFormats.I8:
                raise NotImplementedError("I8 not implemented")
            case GCNTextureFormats.IA4:
                raise NotImplementedError("IA4 not implemented")
            case GCNTextureFormats.IA8:
                raise NotImplementedError("IA8 not implemented")
            case GCNTextureFormats.RGB565:
                raise NotImplementedError("RGB565 not implemented")
            case GCNTextureFormats.RGB5A3:
                rgba = img.from_rgb5a3(data, width, height)
                raise NotImplementedError("RGB5A3 not implemented")
            case GCNTextureFormats.RGBA32:
                raise NotImplementedError("RGBA32 not implemented")
            case GCNTextureFormats.C4:
                raise NotImplementedError("C4 not implemented")
            case GCNTextureFormats.C8:
                raise NotImplementedError("C8 not implemented")
            case GCNTextureFormats.CMPR:
                raise NotImplementedError("CMPR not implemented")
        return img.rgba_to_image(rgba, width, height)

        # switch (format)
        # {
        #     case TPL_TextureFormat.I4:
        #         rgba = tmpTpl.fromI4(imageData, width, height);
        #         break;
        #     case TPL_TextureFormat.I8:
        #         rgba = tmpTpl.fromI8(imageData, width, height);
        #         break;
        #     case TPL_TextureFormat.IA4:
        #         rgba = tmpTpl.fromIA4(imageData, width, height);
        #         break;
        #     case TPL_TextureFormat.IA8:
        #         rgba = tmpTpl.fromIA8(imageData, width, height);
        #         break;
        #     case TPL_TextureFormat.RGB565:
        #         rgba = tmpTpl.fromRGB565(imageData, width, height);
        #         break;
        #     case TPL_TextureFormat.RGB5A3:
        #         rgba = tmpTpl.fromRGB5A3(imageData, width, height);
        #         break;
        #     case TPL_TextureFormat.RGBA8:
        #         rgba = tmpTpl.fromRGBA8(imageData, width, height);
        #         break;
        #     case TPL_TextureFormat.CI4:
        #         rgba = new byte[0];
        #         rgba = tmpTpl.fromCI4(imageData, paletteDataRgba, width, height);
        #         break;
        #     case TPL_TextureFormat.CI8:
        #         rgba = new byte[0];
        #         rgba = tmpTpl.fromCI8(imageData, paletteDataRgba, width, height);
        #         break;
        #     case TPL_TextureFormat.CI14X2:
        #         rgba = new byte[0];
        #         rgba = tmpTpl.fromCI14X2(imageData, paletteDataRgba, width, height);
        #         break;
        #     case TPL_TextureFormat.CMP:
        #         rgba = tmpTpl.fromCMP(imageData, width, height);
        #         break;
        #     default:
        #         rgba = new byte[0];
        #         break;
        # }

        # output = tmpTpl.rgbaToImage(rgba, width, height);
        # return output;


class TPLImage:
    """
    See: https://github.com/Ploaj/Metanoia/blob/master/Metanoia/Tools/TLP.cs
    """

    @dataclass
    class PaletteHeader:
        """TODO"""

        num_items: int = 0  # short
        unpacked: int = 0  # byte
        palette_format: GCNPaletteFormats = GCNPaletteFormats.IA8  # uint
        data_ofs: int = -1  # uint

    def palette_to_rgba(self, header: PaletteHeader, data: bytes) -> bytes:
        """TODO"""
        palette_format: GCNPaletteFormats = header.palette_format
        r = g = b = a = 0

        output: list[int] = []

        # print(header)

        for i in range(header.num_items):
            pixel = bytes((data[i * 2 + 1], data[i * 2]))
            pixel = int.from_bytes(pixel, signed=False)

            # print(pixel)

            return
        #     output.append(int.to_bytes(data[8*2+1], length = 2, byteorder="big", signed=False))

        #     ushort pixel = BitConverter.ToUInt16(new byte[] { data[i * 2 + 1], data[i * 2] }, 0);

        #     if (paletteformat == TPL_PaletteFormat.IA8) //IA8
        #     {
        #         r = pixel & 0xff;
        #         b = r;
        #         g = r;
        #         a = pixel >> 8;
        #     }
        #     else if (paletteformat == TPL_PaletteFormat.RGB565) //RGB565
        #     {
        #         b = (((pixel >> 11) & 0x1F) << 3) & 0xff;
        #         g = (((pixel >> 5) & 0x3F) << 2) & 0xff;
        #         r = (((pixel >> 0) & 0x1F) << 3) & 0xff;
        #         a = 255;
        #     }
        #     else //RGB5A3
        #     {
        #         if ((pixel & (1 << 15)) != 0) //RGB555
        #         {
        #             a = 255;
        #             b = (((pixel >> 10) & 0x1F) * 255) / 31;
        #             g = (((pixel >> 5) & 0x1F) * 255) / 31;
        #             r = (((pixel >> 0) & 0x1F) * 255) / 31;
        #         }
        #         else //RGB4A3
        #         {
        #             a = (((pixel >> 12) & 0x07) * 255) / 7;
        #             b = (((pixel >> 8) & 0x0F) * 255) / 15;
        #             g = (((pixel >> 4) & 0x0F) * 255) / 15;
        #             r = (((pixel >> 0) & 0x0F) * 255) / 15;
        #         }
        #     }

        #     output[i] = (uint)((r << 0) | (g << 8) | (b << 16) | (a << 24));
        # }

        # return output;

    def from_rgb5a3(self, data: bytes, width: int, height: int) -> list[int]:
        """TODO"""
        output_pixels: list[int] = [None] * (width * height)
        pixel_data = BytesIO(data)

        for block_y in range(0, (height - 1) // 4 + 1):
            for block_x in range(0, (width - 1) // 4 + 1):
                for y in range(4):
                    if block_y * 4 + y > height:
                        continue
                    for x in range(4):
                        if block_x * 4 + x > width:
                            continue
                        pixel = int.from_bytes(pixel_data.read(0x02), byteorder="big")
                        if pixel >> 15 & 1:
                            # No alpha component
                            a = 0xFF
                            r = 0x08 * (pixel >> 10 & 0x1F)
                            g = 0x08 * (pixel >> 5 & 0x1F)
                            b = 0x08 * (pixel >> 0 & 0x1F)
                        else:
                            # Alpha component
                            a = 0x20 * (pixel >> 12 & 0x07)
                            r = 0x11 * (pixel >> 8 & 0x0F)
                            g = 0x11 * (pixel >> 4 & 0x0F)
                            b = 0x11 * (pixel >> 0 & 0x0F)
                        index = width * y + x + block_x * 4 + block_y * (width * 4)
                        output_pixels[index] = r << 24 | g << 16 | b << 8 | a << 0
                        # print(
                        #     f"index={index}\ti={i}, block_x={block_x}, block_y={block_y}, x={x}, y={y}"
                        # )
                        # if i > 256:
                        #     exit(0)

        print(f"wrote {width*height} pixels")
        img = Image.frombytes(
            "RGBA",
            (width, height),
            b"".join([int.to_bytes(pixel, 4) for pixel in output_pixels]),
        )
        img.show()
        exit(0)

        inp = 0
        r, g, b, a = 0, 0, 0, 0

        for y in range(0, height, 4):
            for x in range(0, width, 4):
                for y1 in range(y, y + 4):
                    for x1 in range(x, x + 4):
                        pass

        #                 ushort pixel = Shared.Swap(BitConverter.ToUInt16(tpl, inp++ * 2));

        #                 if (y1 >= height || x1 >= width)
        #                     continue;

        #                 if ((pixel & (1 << 15)) != 0)
        #                 {
        #                     b = (((pixel >> 10) & 0x1F) * 255) / 31;
        #                     g = (((pixel >> 5) & 0x1F) * 255) / 31;
        #                     r = (((pixel >> 0) & 0x1F) * 255) / 31;
        #                     a = 255;
        #                 }
        #                 else
        #                 {
        #                     a = (((pixel >> 12) & 0x07) * 255) / 7;
        #                     b = (((pixel >> 8) & 0x0F) * 255) / 15;
        #                     g = (((pixel >> 4) & 0x0F) * 255) / 15;
        #                     r = (((pixel >> 0) & 0x0F) * 255) / 15;
        #                 }

        #                 output[(y1 * width) + x1] = (uint)((r << 0) | (g << 8) | (b << 16) | (a << 24));
        #             }
        #         }
        #     }
        # }

        # return Shared.UIntArrayToByteArray(output);

    def rgba_to_image(self, data: bytes, width: int, height: int) -> BitMapImage:
        """TODO"""

        #  if (width == 0) width = 1;
        # if (height == 0) height = 1;

        # Bitmap bmp = new Bitmap(width, height, System.Drawing.Imaging.PixelFormat.Format32bppArgb);

        # try
        # {
        #     System.Drawing.Imaging.BitmapData bmpData = bmp.LockBits(
        #                             new Rectangle(0, 0, bmp.Width, bmp.Height),
        #                             System.Drawing.Imaging.ImageLockMode.WriteOnly, bmp.PixelFormat);

        #     System.Runtime.InteropServices.Marshal.Copy(data, 0, bmpData.Scan0, data.Length);
        #     bmp.UnlockBits(bmpData);
        # }
        # catch { bmp.Dispose(); throw; }

        # return bmp;
