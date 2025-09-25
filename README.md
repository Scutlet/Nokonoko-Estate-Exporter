# Nokonoko-Estate-Exporter
A Mario Party 8 HSF-to-DAE exporter. While Mario Party 4 through 8 are all developed by the same publisher and use the same (or a similar) file format, this tool specifically focussed on compatibility with Mario Party 8.

## Support
Currently supports exporting specific information to DAE. These files can be extracted from the game's `.bin` files using [mpbindump](https://github.com/gamemasterplc/mpbindump)

**HSF**:
- Meshes, including duplicates that reference the same geometry
- Vertex colors
- Vertex normals
- Textures

### Unsupported
**HSF**:
- Cameras
- Lights
- Armature/bones/weights
- Animations/motions

**ANM** (Animations)
- Anything

**DAT** (likely used to set up board squares; unverified)
- Anything

## References
Most of the format was deciphered using other available tools or data sources, including:
- [Metanoia](https://github.com/Ploaj/Metanoia)
- [MPLibrary](https://github.com/KillzXGaming/MPLibrary)
- [Mario Party 5 Decompilation](https://github.com/mariopartyrd/marioparty5)
- [hsfview](https://github.com/gamemasterplc/hsfview)
