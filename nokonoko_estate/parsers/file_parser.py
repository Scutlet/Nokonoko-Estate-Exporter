from copy import deepcopy
import io
import logging

from PIL import Image

from nokonoko_estate.formats.enums import GCNPaletteFormat, GCNTextureFormat
from nokonoko_estate.formats.formats import (
    AttributeHeader,
    HSFAttributes,
    HSFNode,
    NodeTransform,
    HSFData,
    HSFFile,
    HSFNodeType,
    MaterialObject,
    AttributeObject,
    MeshObject,
    HSFNodeData,
    PaletteInfo,
    PrimitiveObject,
    TextureInfo,
    Vertex,
)
from nokonoko_estate.parsers.base import HSFParserBase
from nokonoko_estate.parsers.parsers import (
    AttributeHeaderParser,
    HSFHeaderParser,
    HSFNodeParser,
    MaterialObjectParser,
    AttributeParser,
    PaletteInfoParser,
    TextureInfoParser,
    VertexParser,
)
from nokonoko_estate.parsers.textures import BitMapImage, get_texture_byte_size

logger = logging.Logger(__name__)
PrimitiveType = PrimitiveObject.PrimitiveType


class HSFFileParser(HSFParserBase[HSFFile]):
    """Parses Mario Party 8 HSF files"""

    def __init__(self, filepath: str) -> None:
        super().__init__(None, None)
        self.filepath = filepath

        # There should be only one node without a parent
        self._root_node: HSFNode = None
        self._nodes: list[HSFNode] = []
        # Attribute header index is used as a key TODO: doesn't work properly!
        self._primitives: list[HSFAttributes[PrimitiveObject]] = []
        self._positions: list[HSFAttributes[tuple[float, float, float]]] = []
        self._uvs: list[HSFAttributes[tuple[float, float]]] = []

        self._textures: list[tuple[str, Image.Image]] = []
        self._materials: list[MaterialObject] = []
        self._attributes: list[AttributeObject] = []

        # symbol indices (reference children)
        self._symbols: list[int] = []

    def parse_from_file(self) -> HSFFile:
        """TODO"""
        with open(self.filepath, "rb") as fl:
            self._fl = fl
            self.parse()
            return self._output_file()

    def _output_file(self):
        """TODO"""
        return HSFFile(
            self._nodes,
            self._textures,
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
        self._primitives = self._parse_primitives(primitive_headers)
        print(f"{len(self._primitives)} primitives identified!")

        # Materials
        self._fl.seek(self._header.materials.offset, io.SEEK_SET)
        self._materials = self._parse_array(
            MaterialObjectParser, self._header.materials.length
        )
        print(f"Identified {len(self._materials)} Material(s)")

        # Attributes TODO
        self._fl.seek(self._header.attributes.offset, io.SEEK_SET)
        self._attributes = self._parse_array(
            AttributeParser, self._header.attributes.length
        )
        print(f"Identified {len(self._attributes)} attributes(s)")

        # (Vertex) positions
        self._fl.seek(self._header.positions.offset, io.SEEK_SET)
        position_headers = self._parse_array(
            AttributeHeaderParser, self._header.positions.length
        )
        self._positions = self._parse_positions(position_headers)
        print(f"Identified {len(self._positions)} position(s)")

        # (Face) Normals TODO
        self._fl.seek(self._header.normals.offset, io.SEEK_SET)
        normal_headers = self._parse_array(
            AttributeHeaderParser, self._header.normals.length
        )
        self._parse_normals(normal_headers)
        # print(f"Identified {len(self.)} normal(s)")

        # (Vertex) UV's TODO
        self._fl.seek(self._header.uvs.offset, io.SEEK_SET)
        uv_headers = self._parse_array(AttributeHeaderParser, self._header.uvs.length)
        self._uvs = self._parse_uvs(uv_headers)
        print(f"Identified {len(self._uvs)} UV(s)")

        # Symbols
        self._fl.seek(self._header.symbols.offset)
        self._symbols = []
        for _ in range(self._header.symbols.length):
            self._symbols.append(self._parse_int(signed=True))
        print(f"Identified {len(self._symbols)} symbol(s)")

        # Nodes (these tie everything together)
        self._fl.seek(self._header.nodes.offset)
        self._nodes = self._parse_nodes()
        print(f"Identified {len(self._nodes)} node(s)")
        for node in self._nodes:
            self._setup_node_references(node)
        # Can only verify once all references have been set up
        for node in self._nodes:
            self._verify_node_references(node)

        # Textures
        self._fl.seek(self._header.textures.offset, io.SEEK_SET)
        self._parse_textures()

        # ???
        end_ofs = self._header.rigs.offset + self._header.rigs.length * 0x24
        self._fl.seek(self._header.rigs.offset)

        # meshnames = list(self._mesh_objects.keys())
        for i in range(self._header.rigs.length):
            # mesh_obj = self._mesh_objects[meshnames[i]]
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

    def _parse_primitives(
        self, headers: list[AttributeHeader]
    ) -> list[HSFAttributes[PrimitiveObject]]:
        """TODO"""
        ofs = self._fl.tell()
        extra_ofs = self._fl.tell()
        for attr in headers:
            # ???
            # AttributeHeader data is size 48?
            extra_ofs += 48 * attr.data_count

        result: list[HSFAttributes[PrimitiveObject]] = []
        for attr in headers:
            prim_name = self._parse_from_stringtable(attr.string_offset, -1)
            primitives = []
            result.append(HSFAttributes(prim_name, primitives))

            self._fl.seek(ofs + attr.data_offset)
            for _ in range(attr.data_count):
                primitive_type = PrimitiveType(self._parse_short())
                prim = PrimitiveObject(primitive_type)
                primitives.append(prim)
                prim.flags = self._parse_short()
                prim.material_index = prim.flags & 0xFFF
                prim.flag_value = prim.flags >> 12

                if primitive_type in (
                    PrimitiveType.PRIMITIVE_TRIANGLE,
                    PrimitiveType.PRIMITIVE_QUAD,
                ):
                    # Triangles have an extra (empty) vertex
                    prim.vertices = self._parse_array(VertexParser, 4)
                elif primitive_type == PrimitiveType.PRIMITIVE_TRIANGLE_STRIP:
                    raise NotImplementedError("Cannot parse triangle strips")
                    # num_vertices = self._parse_int()
                    # ofs = self._parse_int()
                    # xxx = self._fl.tell()
                    # self._fl.seek(extra_ofs + ofs * 8, io.SEEK_SET)
                    # vertices = self._parse_array(VertexParser, num_vertices)
                    # self._fl.seek(xxx)
                    # prim_obj.tri_count = len(prim_obj.vertices)

                    # # ???
                    # # size: length(vertices) + num_vertices + 1
                    # new_vert: list[Vertex] = deepcopy(prim_obj.vertices)
                    # new_vert[3] = new_vert[1]
                    # new_vert += deepcopy(vertices)
                    # prim_obj.vertices = new_vert
                else:
                    raise NotImplementedError(f"Cannot parse {primitive_type}")

                prim.nbt_data = (
                    self._parse_int(),
                    self._parse_int(),
                    self._parse_int(),
                )
        return result

    def _parse_positions(
        self, headers: list[AttributeHeader]
    ) -> list[HSFAttributes[tuple[float, float, float]]]:
        """TODO"""
        start_ofs = self._fl.tell()
        result: list[HSFAttributes[tuple[float, float, float]]] = []
        for attr in headers:
            name = self._parse_from_stringtable(attr.string_offset, -1)
            positions: list[tuple[float, float, float]] = []
            result.append(HSFAttributes(name, positions))

            self._fl.seek(start_ofs + attr.data_offset)
            for _ in range(attr.data_count):
                positions.append(
                    # Parses raw bytes in Metanoia, instead of floats
                    (self._parse_float(), self._parse_float(), self._parse_float())
                )
        return result

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

        for i, attr in enumrate(headers):
            ofs = self._fl.seek(start_ofs + attr.data_offset)
            normals: list[tuple[int, int, int]] = []
            for j in range(attr.data_count):
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
                raise ValueError()
                self._mesh_objects[name] = MeshObject(name)
            self._mesh_objects[name][i].normals += normals
            print(f"Parsed {len(normals)} (vertex) normals for mesh {name}")

    def _parse_uvs(
        self, headers: list[AttributeHeader]
    ) -> list[HSFAttributes[tuple[float, float]]]:
        start_ofs = self._fl.tell()

        result: list[HSFAttributes[tuple[float, float]]] = []
        for attr in headers:
            name = self._parse_from_stringtable(attr.string_offset, -1)
            uv_coords: list[tuple[float, float]] = []
            result.append(HSFAttributes(name, uv_coords))

            self._fl.seek(start_ofs + attr.data_offset)
            for _ in range(attr.data_count):
                uv_coords.append(
                    # Parses raw bytes in Metanoia, instead of floats
                    (self._parse_float(), self._parse_float())
                )
                # print(f"{uv_coords[i]}")
        return result

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

            # print(f"> Identified texture {tex_name} ({format.name})")
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

    def _parse_nodes(self):
        """TODO"""
        node_len = self._header.nodes.length
        nodes: list[HSFNode] = []
        for _ in range(node_len):
            nodes.append(HSFNode(HSFNodeParser(self._fl, self._header).parse()))
        return nodes

    def _setup_node_references(self, node: HSFNode):
        """
        Ties all node index references to related objects.
        Requires the following to be set:
        - `self._nodes`
        - `self._primitives`
        - `self._positions`
        - `self._uvs`
        """
        if node.node_data.type == HSFNodeType.MESH:
            self._setup_mesh_references(node)

        if not node.has_hierarchy:
            # Cameras and Lights don't have parents/children
            return

        # Set easy access to parent
        if node.node_data.parent_index != -1:
            node.parent = self._nodes[node.node_data.parent_index]
        else:
            self._root_node = node

        # Children are listed directly after the parent in the symbol indices
        for i in range(node.node_data.children_count):
            child_index = self._symbols[node.node_data.symbol_index + i]
            child = self._nodes[child_index]
            node.children.append(child)

    def _setup_mesh_references(self, node: HSFNode):
        """TODO"""
        # Primitives
        primitives_index = node.node_data.primitives_index
        assert (
            primitives_index != -1
        ), f"Expected primitives to be present for node {node}"
        primitives = self._primitives[primitives_index]

        # Positions
        positions_index = node.node_data.positions_index
        assert (
            positions_index != -1
        ), f"Expected positions to be present for node {node}"
        positions = self._positions[positions_index]

        # UV coords
        uv_index = node.node_data.uv_index
        # UVs may not be present
        uv_indices_data = []
        if uv_index != -1:
            uv_indices_data = self._uvs[uv_index].data

        # Vertex Colors
        # TODO

        # Attributes
        attribute_index = node.node_data.attribute_index
        attribute = None
        if attribute_index != -1:
            attribute = self._attributes[attribute_index]

        # print(node.node_data.type.name, primitives_index, positions_index, uv_index)

        # Yet another sanity check. TODO: move
        expected_name = primitives.name
        for attributes in (positions,):
            assert (
                attributes.name == expected_name
            ), f"Encountered a name difference {attributes.name} vs {expected_name}"

        node.mesh_data = MeshObject(expected_name)
        node.mesh_data.primitives = primitives.data
        node.mesh_data.positions = positions.data
        node.mesh_data.uvs = uv_indices_data
        node.attribute = attribute

    def _verify_node_references(self, node: HSFNode):
        """Verifies that referenced indices are set up correctly. This is just a sanity check."""
        # If a node has a parent, the node a child of its parent
        if node.parent is not None:
            assert (
                node in node.parent.children
            ), "Node has a parent, but isn't a child of that parent"
        elif node.has_hierarchy:
            assert (
                node == self._root_node
            ), f"Node ({node}) has no parent, but isn't the root node: {self._root_node})"
        # All children have their parent correctly set
        for child in node.children:
            assert (
                child.parent == node
            ), "Node has children, but isn't a parent for one of them"
