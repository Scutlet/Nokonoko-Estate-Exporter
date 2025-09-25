from enum import Enum


class GCNTextureFormat(Enum):
    """
    ImageFormat specifies how the data within the image is encoded.
    Included is a chart of how many bits per pixel there are,
    the width/height of each block, how many bytes long the
    actual block is, and a description of the type of data stored.
    See: https://wiki.tockdom.com/wiki/Image_Formats
    See: https://github.com/KillzXGaming/Toolbox.Core/blob/3262957308e49a614fb5337eeb954993d76527fa/src/Textures/Swizzle/Gamecube/Decode_Gamecube.cs
    """

    # Bits per Pixel | Block Width | Block Height | Block Size | Type / Description
    I4 = 0x00  #  4 | 8 | 8 | 32 | grey
    I8 = 0x01  #  8 | 8 | 8 | 32 | grey
    IA4 = 0x02  #  8 | 8 | 4 | 32 | grey + alpha
    IA8 = 0x03  # 16 | 4 | 4 | 32 | grey + alpha
    RGB565 = 0x04  # 16 | 4 | 4 | 32 | color
    RGB5A3 = 0x05  # 16 | 4 | 4 | 32 | color + alpha
    RGBA32 = 0x06  # 32 | 4 | 4 | 64 | color + alpha
    C4 = 0x08  #  4 | 8 | 8 | 32 | palette choices (IA8, RGB565, RGB5A3)
    C8 = 0x09  #  8 | 8 | 4 | 32 | palette choices (IA8, RGB565, RGB5A3)
    C14X2 = 0x0A  # 16 | 4 | 4 | 32 | palette (IA8, RGB565, RGB5A3) NOTE: only 14 bits are used per pixel
    CMPR = 0x0E  #  4 | 8 | 8 | 32 | mini palettes in each block, RGB565 or transparent.


class GCNPaletteFormat(Enum):
    """
    PaletteFormat specifies how the data within the palette is stored. An
    image uses a single palette (except CMPR which defines its own
    mini-palettes within the Image data). Only C4, C8, and C14X2 use
    palettes. For all other formats the type and count is zero.
    See: https://wiki.tockdom.com/wiki/Image_Formats#Palette_Formats
    See: https://github.com/KillzXGaming/Toolbox.Core/blob/3262957308e49a614fb5337eeb954993d76527fa/src/Textures/Swizzle/Gamecube/Decode_Gamecube.cs
    """

    IA8 = 0x00
    RGB565 = 0x01
    RGB5A3 = 0x02


class CombinerBlend(Enum):
    """Blend modes for Material Attributes"""

    # Mixes current and last stages by texture alpha with a new stage
    TRANSPARENCY_MIX = 0

    # Combines current and last stage by adding.
    ADDITIVE = 2


class WrapMode(Enum):
    """Texture wrapping"""

    CLAMP = 0
    REPEAT = 1
    MIRROR = 2
