from copy import deepcopy
import io
import logging

from PIL import Image

from nokonoko_estate.formats.enums import GCNPaletteFormat, GCNTextureFormat
from nokonoko_estate.formats.formats import (
    AttributeHeader,
    HSFData,
    HSFFile,
    MaaterialObject,
    AttributeObject,
    MeshObject,
    BoneObject,
    PaletteInfo,
    PrimitiveObject,
    TextureInfo,
    Vertex,
)
from nokonoko_estate.parsers.base import HSFParserBase
from nokonoko_estate.parsers.parsers import (
    AttributeHeaderParser,
    HSFHeaderParser,
    MaterialObjectParser,
    AttributeParser,
    PaletteInfoParser,
    TextureInfoParser,
    VertexParser,
)
from nokonoko_estate.parsers.textures import BitMapImage, get_texture_byte_size

logger = logging.Logger(__name__)


class HSFFileParser(HSFParserBase[HSFFile]):
    """Parses Mario Party 8 HSF files"""

    def __init__(self, filepath: str) -> None:
        super().__init__(None, None)
        self.filepath = filepath

        self._mesh_objects: dict[str, MeshObject] = {}
        self._textures: list[tuple[str, Image.Image]] = []
        self._bones: list[BoneObject] = []
        self._materials: list[MaaterialObject] = []
        self._attributes: list[AttributeObject] = []

    def parse_from_file(self) -> HSFFile:
        """TODO"""
        with open(self.filepath, "rb") as fl:
            self._fl = fl
            self.parse()
            return self._output_file()

    def _output_file(self):
        """TODO"""
        return HSFFile(
            self._mesh_objects,
            self._textures,
            self._bones,
            self._materials,
            self._attributes,
        )

    def parse(self) -> HSFFile:
        self._header = HSFHeaderParser(self._fl).parse()
        # print(self._header)

        # Primitives
        self._fl.seek(self._header.primitives.offset, io.SEEK_SET)
        primitive_headers = self._parse_array(
            AttributeHeaderParser, self._header.primitives.length
        )
        self._parse_primitives(primitive_headers)

        # Materials
        self._fl.seek(self._header.attributes.offset, io.SEEK_SET)
        self._attributes = self._parse_array(
            AttributeParser, self._header.attributes.length
        )
        print(self._attributes)
        print(f"{len(self._attributes)} attributes identified!")

        # Materials 1
        self._fl.seek(self._header.materials.offset, io.SEEK_SET)
        self._materials = self._parse_array(
            MaterialObjectParser, self._header.materials.length
        )
        print(f"{len(self._materials)} materials identified!")

        # (Vertex) positions
        self._fl.seek(self._header.positions.offset, io.SEEK_SET)
        print(f"Positions start ofs: {self._fl.tell():#x}")
        position_headers = self._parse_array(
            AttributeHeaderParser, self._header.positions.length
        )
        self._parse_positions(position_headers)

        # (Face) Normals
        self._fl.seek(self._header.normals.offset, io.SEEK_SET)
        normal_headers = self._parse_array(
            AttributeHeaderParser, self._header.normals.length
        )
        self._parse_normals(normal_headers)

        # (Vertex) UV's
        self._fl.seek(self._header.uvs.offset, io.SEEK_SET)
        uv_headers = self._parse_array(AttributeHeaderParser, self._header.uvs.length)
        self._parse_uvs(uv_headers)

        # Textures
        self._fl.seek(self._header.textures.offset, io.SEEK_SET)
        self._parse_textures()

        # Bones
        self._fl.seek(self._header.bones.offset)
        self._parse_bones()

        # ???
        end_ofs = self._header.rigs.offset + self._header.rigs.length * 0x24
        self._fl.seek(self._header.rigs.offset)

        meshnames = list(self._mesh_objects.keys())
        for i in range(self._header.rigs.length):
            mesh_obj = self._mesh_objects[meshnames[i]]
            raise NotImplementedError("Rigging not implemented")

        # uint endOffset = rigOffset + (uint)(rigCount * 0x24);
        # reader.Position = rigOffset;
        # var meshName = MeshObjects.Keys.ToArray();
        # for (int i = 0; i < rigCount; i++)
        # {
        #     var mo = MeshObjects[meshName[i]];
        #     reader.Position += 4; // 0xCCCCCCCC
        #     var singleBindOffset = reader.ReadUInt32();
        #     var doubleBindOffset = reader.ReadUInt32();
        #     var multiBindOffset = reader.ReadUInt32();
        #     var singleBindCount = reader.ReadInt32();
        #     var doubleBindCount = reader.ReadInt32();
        #     var multiBindCount = reader.ReadInt32();
        #     var vertexCount = reader.ReadInt32();
        #     mo.SingleBind = reader.ReadInt32();
        #     //Console.WriteLine($"{mo.Name} {Nodes[mo.SingleBind].Name}");

        #     var temp = reader.Position;

        #     reader.Position = endOffset + singleBindOffset;
        #     mo.SingleBinds.AddRange(reader.ReadStructArray<RiggingSingleBind>(singleBindCount));

        #     reader.Position = endOffset + doubleBindOffset;
        #     mo.DoubleBinds.AddRange(reader.ReadStructArray<RiggingDoubleBind>(doubleBindCount));

        #     reader.Position = endOffset + multiBindOffset;
        #     mo.MultiBinds.AddRange(reader.ReadStructArray<RiggingMultiBind>(multiBindCount));

        #     if(i != rigCount - 1)
        #         reader.Position = temp;
        # }

        # var weightStart = reader.Position;
        # for (int i = 0; i < rigCount; i++)
        # {
        #     var mo = MeshObjects[meshName[i]];

        #     foreach (var mb in mo.DoubleBinds)
        #     {
        #         reader.Position = (uint)(weightStart + mb.WeightOffset);
        #         mo.DoubleWeights.AddRange(reader.ReadStructArray<RiggingDoubleWeight>(mb.Count));
        #     }
        # }

        # weightStart = reader.Position;
        # for (int i = 0; i < rigCount; i++)
        # {
        #     var mo = MeshObjects[meshName[i]];

        #     foreach (var mb in mo.MultiBinds)
        #     {
        #         reader.Position = (uint)(weightStart + mb.WeightOffset);
        #         mo.MultiWeights.AddRange(reader.ReadStructArray<RiggingMultiWeight>(mb.Count));
        #     }
        # }

    def _parse_primitives(self, headers: list[AttributeHeader]):
        """TODO"""
        ofs = self._fl.tell()
        extra_ofs = self._fl.tell()
        for attr in headers:
            # ???
            # AttributeHeader data is size 48?
            extra_ofs += 48 * attr.data_count

        meshobj_index = 0
        for attr in headers:
            prim_name = self._parse_from_stringtable(attr.string_offset, -1)
            # print(prim_name)
            if prim_name in self._mesh_objects:
                # Mesh object already parsed
                continue

            mesh_obj = MeshObject(prim_name)
            self._mesh_objects[prim_name] = mesh_obj
            meshobj_index += 1
            # print(f"{mesh_obj.name} contains {attr.data_count} primitive(s)")

            self._fl.seek(ofs + attr.data_offset)
            for i in range(attr.data_count):
                primitive_type = PrimitiveObject.PrimitiveType(self._parse_short())
                material = self._parse_short() & 0xFF
                prim_obj = PrimitiveObject(primitive_type, material)
                self._mesh_objects[prim_name].primitives.append(prim_obj)

                num_vertices = 3
                if primitive_type in (
                    PrimitiveObject.PrimitiveType.PRIMITIVE_TRIANGLE,
                    PrimitiveObject.PrimitiveType.PRIMITIVE_QUAD,
                ):
                    # NB: For w05_file24.hsf, the primitive_type is always 3
                    num_vertices = 4

                prim_obj.vertices = self._parse_array(VertexParser, num_vertices)

                if (
                    primitive_type
                    == PrimitiveObject.PrimitiveType.PRIMITIVE_TRIANGLE_STRIP
                ):
                    raise NotImplementedError()
                    num_vertices = self._parse_int()
                    ofs = self._parse_int()
                    xxx = self._fl.tell()
                    self._fl.seek(extra_ofs + ofs * 8, io.SEEK_SET)
                    vertices = self._parse_array(VertexParser, num_vertices)
                    self._fl.seek(xxx)
                    prim_obj.tri_count = len(prim_obj.vertices)

                    # ???
                    # size: length(vertices) + num_vertices + 1
                    new_vert: list[Vertex] = deepcopy(prim_obj.vertices)
                    new_vert[3] = new_vert[1]
                    new_vert += deepcopy(vertices)
                    prim_obj.vertices = new_vert

                prim_obj.unk = (self._parse_int(), self._parse_int(), self._parse_int())

    def _parse_positions(self, headers: list[AttributeHeader]):
        """TODO"""
        start_ofs = self._fl.tell()
        for attr in headers:
            ofs = self._fl.seek(start_ofs + attr.data_offset)
            positions: list[tuple[float, float, float]] = []
            for i in range(attr.data_count):
                positions.append(
                    # Parses raw bytes in Metanoia, instead of floats
                    (self._parse_float(), self._parse_float(), self._parse_float())
                )
                # print(f"{positions[i]}")

            name = self._parse_from_stringtable(attr.string_offset, -1)
            # print(name)
            if name not in self._mesh_objects:
                self.logger.warning(
                    f"{name} was not present in self._mesh_objects, but some (vertex) positions referenced it!"
                )
                self._mesh_objects[name] = MeshObject(name)
            self._mesh_objects[name].positions += positions
            # print(f"Parsed {len(positions)} (vertex) positions for mesh {name}")

    def _parse_normals(self, headers: list[AttributeHeader]):
        """TODO"""
        return
        start_ofs = self._fl.tell()
        flag = 0
        if len(headers) >= 2:
            # TODO
            # var pos = startingOffset + headers[0].DataOffset + headers[0].DataCount * 3;
            # if (pos % 0x20 != 0)
            #     pos += 0x20 - (pos % 0x20);
            # if (headers[1].DataOffset == pos - startingOffset)
            #     flag = 4;
            raise NotImplementedError()

        for attr in headers:
            ofs = self._fl.seek(start_ofs + attr.data_offset)
            normals: list[tuple[int, int, int]] = []
            for i in range(attr.data_count):
                if flag == 4:
                    # TODO
                    # nrmList.Add(new Vector3(reader.ReadSByte() / (float)sbyte.MaxValue, reader.ReadSByte() / (float)sbyte.MaxValue, reader.ReadSByte() / (float)sbyte.MaxValue));
                    raise NotImplementedError()
                else:
                    normals.append(
                        # Parses raw bytes in Metanoia, instead of floats
                        (self._parse_float(), self._parse_float(), self._parse_float())
                    )
                # print(normals[i])
            name = self._parse_from_stringtable(attr.string_offset, -1)
            # print(name)
            if name not in self._mesh_objects:
                self.logger.warning(
                    f"{name} was not present in self._mesh_objects, but some (face) normals referenced it!"
                )
                self._mesh_objects[name] = MeshObject(name)
            self._mesh_objects[name].normals += normals
            print(f"Parsed {len(normals)} (vertex) normals for mesh {name}")

    def _parse_uvs(self, headers: list[AttributeHeader]):
        start_ofs = self._fl.tell()

        for attr in headers:
            ofs = self._fl.seek(start_ofs + attr.data_offset)
            uv_coords: list[tuple[int, int]] = []
            for i in range(attr.data_count):
                uv_coords.append(
                    # Parses raw bytes in Metanoia, instead of floats
                    (self._parse_float(), self._parse_float())
                )
                # print(f"{uv_coords[i]}")

            name = self._parse_from_stringtable(attr.string_offset, -1)
            # print(name)
            if name not in self._mesh_objects:
                self.logger.warning(
                    f"{name} was not present in self._mesh_objects, but some (vertex) UV referenced it!"
                )
                self._mesh_objects[name] = MeshObject(name)
            self._mesh_objects[name].uvs += uv_coords
            # print(f"Parsed {len(uv_coords)} (vertex) UV's for mesh {name}")

    def _parse_textures(self):
        """TODO"""
        tex_len = self._header.textures.length
        pal_ofs = self._header.palettes.offset
        pal_len = self._header.palettes.length

        tex_infos: list[TextureInfo] = self._parse_array(TextureInfoParser, tex_len)
        ofs_post_tex = self._fl.tell()
        print(f"Identified {tex_len} texture(s)")

        self._fl.seek(pal_ofs, io.SEEK_SET)
        pal_infos: list[PaletteInfo] = self._parse_array(PaletteInfoParser, pal_len)
        ofs_post_pal = self._fl.tell()
        print(f"Identified {pal_len} palette(s)")
        # print(
        #     "\n".join(
        #         [
        #             str(x) + self._parse_from_stringtable(x.name_offset)
        #             for x in pal_infos
        #         ]
        #     )
        # )

        for tex_info in tex_infos:
            tex_name = self._parse_from_stringtable(tex_info.name_offset, -1)

            format: GCNTextureFormat = None
            match tex_info.tex_format:
                case 0x00 | 0x01 | 0x02 | 0x03 | 0x04 | 0x05 | 0x06:
                    format = GCNTextureFormat(tex_info.tex_format)
                case 0x07:
                    format = GCNTextureFormat.CMPR
                case 0x09 | 0x0A | 0x0B:
                    format = GCNTextureFormat.C8
                case _:
                    raise NotImplementedError(
                        f"Invalid tex_format found for {tex_name}: {tex_info.tex_format}"
                    )
            if format == GCNTextureFormat.C8 and tex_info.bpp == 4:
                format = GCNTextureFormat.C4

            print(f"> Identified texture {tex_name} ({format.name})")
            pal_data: bytes = bytes()
            pal_format: GCNPaletteFormat | None = None
            match tex_info.tex_format:
                case 0x00:
                    # No palette
                    pass
                case 0x09:
                    pal_format = GCNPaletteFormat.RGB565
                case 0x0A:
                    pal_format = GCNPaletteFormat.RGB5A3
                case 0x0B:
                    pal_format = GCNPaletteFormat.IA8

            if tex_info.palette_index >= 0:
                pal_info = pal_infos[tex_info.palette_index]
                prev_ofs = self._fl.tell()
                self._fl.seek(ofs_post_pal + pal_info.data_offset, io.SEEK_SET)
                pal_data = self._fl.read(2 * pal_info.count)
                self._fl.seek(prev_ofs, io.SEEK_SET)

            data_sz = get_texture_byte_size(format, tex_info.width, tex_info.height)
            self._fl.seek(ofs_post_tex + tex_info.data_offset, io.SEEK_SET)
            data = self._fl.read(data_sz)

            bitmap = BitMapImage.convert_from_texture(
                data, tex_info.width, tex_info.height, format, pal_data, pal_format
            )

            if bitmap is not None:
                self._textures.append((tex_name, bitmap))

    def _parse_bones(self):
        """TODO"""
        bone_len = self._header.bones.length
        print(f"Identified {bone_len} bone(s)")
        for i in range(bone_len):
            str_ofs = self._parse_int()
            name = self._parse_from_stringtable(str_ofs, -1)

            bone = BoneObject(name)
            self._bones.append(bone)
            bone.type = self._parse_int()
            self._fl.seek(0x08, io.SEEK_CUR)  # ???
            bone.parent_index = self._parse_int()
            if bone.parent_index < 0 and bone.parent_index != -1:
                bone.parent_index = -1
                raise ValueError(f"Bone's parent_index negative: {bone.parent_index}")

            self._fl.seek(0x08, io.SEEK_CUR)  # ???
            bone.position = (
                self._parse_float(),
                self._parse_float(),
                self._parse_float(),
            )
            bone.rotation = (
                self._parse_float(),
                self._parse_float(),
                self._parse_float(),
            )
            bone.scale = (self._parse_float(), self._parse_float(), self._parse_float())

            self._fl.seek(0xD4, io.SEEK_CUR)  # ???
            bone.material_index = self._parse_int()
            self._fl.seek(0x2C, io.SEEK_CUR)  # ???
