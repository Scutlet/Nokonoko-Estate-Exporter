from copy import deepcopy
import io
import logging
import os

from PIL import Image

from nokonoko_estate.formats.enums import GCNPaletteFormat, GCNTextureFormat
from nokonoko_estate.formats.formats import (
    AttributeHeader,
    BezierKeyFrame,
    HSFAttributes,
    HSFEnvelope,
    HSFNode,
    HSFMotionDataHeader,
    HSFRigHeader,
    HSFTrackData,
    InterpolationMode,
    KeyFrame,
    MotionTrackEffect,
    MotionTrackMode,
    HSFFile,
    HSFNodeType,
    MaterialObject,
    AttributeObject,
    HSFPaletteHeader,
    PrimitiveObject,
    HSFTextureHeader,
    SkeletonObject,
    Vertex,
)
from nokonoko_estate.parsers.base import HSFParserBase
from nokonoko_estate.parsers.parser_log import ParserLogger
from nokonoko_estate.parsers.parsers import (
    AttributeHeaderParser,
    HSFHeaderParser,
    HSFNodeParser,
    MaterialObjectParser,
    AttributeParser,
    MotionDataHeaderParser,
    PaletteHeaderParser,
    RigHeaderParser,
    RiggingDoubleBindParser,
    RiggingDoubleWeightParser,
    RiggingMultiBindParser,
    RiggingMultiWeightParser,
    RiggingSingleBindParser,
    SkeletonParser,
    TextureHeaderParser,
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
        self._non_hierarchy_nodes: list[HSFNode] = []
        self._nodes: list[HSFNode] = []
        self._primitives: list[HSFAttributes[PrimitiveObject]] = []
        self._positions: list[HSFAttributes[tuple[float, float, float]]] = []
        self._normals: list[HSFAttributes[tuple[float, float, float]]] = []
        self._uvs: list[HSFAttributes[tuple[float, float]]] = []
        self._colors: list[HSFAttributes[tuple[float, float, float, float]]] = []
        self._envelopes: list[HSFEnvelope] = []
        self._skeletons: list[SkeletonObject] = []

        self._textures: list[tuple[str, Image.Image]] = []
        self._materials: list[MaterialObject] = []
        self._attributes: list[AttributeObject] = []

        # symbol indices (reference children)
        self._symbols: list[int] = []

        self._fl: ParserLogger = None

    def get_parselog(self):
        return self._fl.parselog

    def parse_from_file(self) -> HSFFile:
        """Parse data from a file"""
        sz = os.path.getsize(self.filepath)
        with open(self.filepath, "rb") as fl:
            self._fl = ParserLogger(fl, sz)
            return self.parse()

    def _output_file(self):
        """TODO"""

        # for i, node in enumerate(self._nodes):
        #     if node.type == HSFNodeType.REPLICA:
        #         print(
        #             node.type.name,
        #             i,
        #             node,
        #             node.hierarchy_data.symbol_index,
        #         )
        #         print("^-- FOUND REPLICA NODE --^")
        #         # exit(-1)
        # print("Didn't find replica...")
        # print("Non-hierarchy nodes:")
        for node in self._non_hierarchy_nodes:
            print(f"| {node} > {node.light_data} {node.camera_data}")

        print("HSF tree:")
        for node, level in self._root_node.dfs():
            print(
                f"|{'-' * 4 * level} {node} @ {node.hierarchy_data.base_transform.position}"
            )

        return HSFFile(
            self._root_node,
            self._nodes,
            self._textures,
            self._materials,
            self._attributes,
        )

    def parse(self) -> HSFFile:
        self._header = HSFHeaderParser(self._fl).parse()

        # Nodes (these tie everything together; we may need these later on)
        self._fl.seek(self._header.nodes.offset)
        self._nodes = self._parse_nodes()
        print(f"Identified {len(self._nodes)} node(s)")

        # Primitives
        self._fl.seek(self._header.primitives.offset, io.SEEK_SET)
        primitive_headers = self._parse_array(
            AttributeHeaderParser, self._header.primitives.length
        )
        self._primitives = self._parse_primitives(primitive_headers)
        print(f"Identified {len(self._primitives)} primitive(s)")

        # Materials
        self._fl.seek(self._header.materials.offset, io.SEEK_SET)
        self._materials = self._parse_array(
            MaterialObjectParser, self._header.materials.length
        )
        print(f"Identified {len(self._materials)} Material(s)")

        # Attributes
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

        # (Vertex) Normals
        self._fl.seek(self._header.normals.offset, io.SEEK_SET)
        normal_headers = self._parse_array(
            AttributeHeaderParser, self._header.normals.length
        )
        self._normals = self._parse_normals(normal_headers, self._nodes)
        print(f"Identified {len(self._normals)} normal(s)")

        # (Vertex) UV's
        self._fl.seek(self._header.uvs.offset, io.SEEK_SET)
        uv_headers = self._parse_array(AttributeHeaderParser, self._header.uvs.length)
        self._uvs = self._parse_uvs(uv_headers)
        print(f"Identified {len(self._uvs)} UV(s)")

        # (Vertex) Colors
        self._fl.seek(self._header.colors.offset, io.SEEK_SET)
        colors = self._parse_array(AttributeHeaderParser, self._header.colors.length)
        self._colors = self._parse_colors(colors)
        print(f"Identified {len(self._colors)} colors(s)")

        # Symbols (for children)
        self._fl.seek(self._header.symbols.offset)
        self._symbols = []
        for _ in range(self._header.symbols.length):
            self._symbols.append(self._parse_int(signed=True))
        print(f"Identified {len(self._symbols)} symbol(s)")

        # Skeletons
        print(f"Identified {self._header.skeletons.length} skeleton(s)")
        self._fl.seek(self._header.skeletons.offset, io.SEEK_SET)
        self._skeletons = self._parse_skeletons()
        import pprint

        pprint.pprint(self._skeletons)
        # print(self._skeletons)

        # Rigs/cenv
        self._fl.seek(self._header.rigs.offset, io.SEEK_SET)
        self._envelopes = self._parse_rigs()

        # Setup node references; these make it easier to reference other data
        for node in self._nodes:
            self._setup_node_references(node)
        # Can only verify once all references have been set up
        for node in self._nodes:
            self._verify_node_references(node)

        # Motions
        self._fl.seek(self._header.motions.offset, io.SEEK_SET)
        self._parse_motions()

        # Textures
        self._fl.seek(self._header.textures.offset, io.SEEK_SET)
        self._parse_textures()
        return self._output_file()

    def _parse_primitives(
        self, headers: list[AttributeHeader]
    ) -> list[HSFAttributes[PrimitiveObject]]:
        """Parses primitives from the HSF-file"""
        base_ofs = self._fl.tell()
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

            self._fl.seek(base_ofs + attr.data_offset)
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
                    prim.vertices = self._parse_array(VertexParser, 3)
                    num_vertices = self._parse_int()
                    ofs = self._parse_int()

                    cur_ofs = self._fl.tell()
                    self._fl.seek(extra_ofs + ofs * 8, io.SEEK_SET)
                    vertices = self._parse_array(VertexParser, num_vertices)
                    self._fl.seek(cur_ofs)
                    prim.tri_count = len(prim.vertices)

                    new_vert: list[Vertex] = deepcopy(prim.vertices)
                    # The winding order of the first triangle is different. Add an extra element so the 2nd/3rd triangle connect to the right vertex
                    new_vert.append(new_vert[1])
                    new_vert += deepcopy(vertices)
                    prim.vertices = new_vert
                else:
                    raise NotImplementedError(f"Cannot parse {primitive_type}")

                prim.nbt_data = (
                    self._parse_int(),
                    self._parse_int(),
                    self._parse_int(),
                )

                self._sanity_check_primitive(prim_name, prim)
        return result

    def _sanity_check_primitive(self, prim_name: str, prim: PrimitiveObject):
        """TODO"""
        # Sanity check for UV-formatting; either all vertices have a UV-index set, or none have
        has_vertex_without_uv = False
        has_vertex_with_uv = False
        vertices = (
            prim.vertices
            if prim.primitive_type != PrimitiveType.PRIMITIVE_TRIANGLE
            else prim.vertices[:3]  # Ignore fourth unused vertex (always empty)
        )
        for v in vertices:
            if v.uv_index == -1:
                has_vertex_without_uv = True
            else:
                has_vertex_with_uv = True
        if has_vertex_without_uv and has_vertex_with_uv:
            # Shouldn't happen
            print(
                f"WARN: Unknown behaviour in primitive {prim_name} ({prim.primitive_type.name}) identified! Found vertex with UV-coordinates defined and vertex without them defined. UV-indices (if unset) will be set to 0 instead. Vertices: {prim.vertices}"
            )
            for v in vertices:
                if v.uv_index == -1:
                    v.uv_index = 0

    def _parse_positions(
        self, headers: list[AttributeHeader]
    ) -> list[HSFAttributes[tuple[float, float, float]]]:
        """Parse vertex positions."""
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

    def _parse_normals(self, headers: list[AttributeHeader], nodes: list[HSFNode]):
        """Parse vertex normals."""
        start_ofs = self._fl.tell()
        result: list[HSFAttributes[tuple[float, float, float]]] = []

        # The way normals should be parsed depends on the node that uses it!
        for node in nodes:
            if node.type != HSFNodeType.MESH:
                continue
            nrm_index = node.mesh_data.nrm_index
            if nrm_index <= -1:
                continue
            # Sanity check
            if nrm_index >= len(headers):
                print(
                    f"WARN: In {node} ({node.type.name}) Attempted to index into normals[{nrm_index:#x}] while there are only {len(headers)} normals!"
                )
                continue
            # TODO: If multiple nodes use the same normals, they are parsed multiple times
            attr = headers[nrm_index]
            normals: list[tuple[float, float, float]] = []
            name = self._parse_from_stringtable(attr.string_offset, -1)
            result.append(HSFAttributes(name, normals))

            self._fl.seek(start_ofs + attr.data_offset)
            for _ in range(attr.data_count):
                if node.mesh_data.cenv_count == 0:
                    normals.append(
                        (
                            self._parse_byte(signed=True) / 127,
                            self._parse_byte(signed=True) / 127,
                            self._parse_byte(signed=True) / 127,
                        )
                    )
                else:
                    # print("!!!!!!!!!")
                    # TODO: verify
                    normals.append(
                        (self._parse_float(), self._parse_float(), self._parse_float())
                    )

            # TODO: Verify whether there are multiple nodes with the same nrm_idx, but with a different value for cenvCount!
        # print(result)
        return result

    def _parse_uvs(
        self, headers: list[AttributeHeader]
    ) -> list[HSFAttributes[tuple[float, float]]]:
        """Parse UV-coordinates"""
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
        return result

    def _parse_colors(
        self, headers: list[AttributeHeader]
    ) -> list[HSFAttributes[tuple[float, float, float, float]]]:
        """Parse vertex colors"""
        start_ofs = self._fl.tell()

        result: list[HSFAttributes[tuple[float, float, float, float]]] = []
        for attr in headers:
            name = self._parse_from_stringtable(attr.string_offset, -1)
            color: list[tuple[float, float]] = []
            result.append(HSFAttributes(name, color))

            self._fl.seek(start_ofs + attr.data_offset)
            for _ in range(attr.data_count):
                color.append(
                    (
                        self._parse_byte() / 255,
                        self._parse_byte() / 255,
                        self._parse_byte() / 255,
                        self._parse_byte() / 255,
                    )
                )
        return result

    def _parse_motions(self):
        """Parse animation data"""
        motions: list[HSFMotionDataHeader] = self._parse_array(
            MotionDataHeaderParser, self._header.motions.length
        )
        start_ofs = self._fl.tell()
        print(f"Identified {len(motions)} motion(s)")

        for motion in motions:
            name = self._parse_from_stringtable(motion.string_offset, -1)
            print(
                f"> Parsing motion: {name} ({motion.track_count} tracks, {motion.motion_length} frames)"
            )

            self._fl.seek(start_ofs + motion.track_data_offset)
            for i in range(motion.track_count):
                mode = MotionTrackMode(self._parse_byte())
                track = HSFTrackData(mode)
                track.unk = self._parse_byte()
                track.string_offset = self._parse_index(size=2)
                track.value_index = self._parse_short(signed=True)
                track.effect = MotionTrackEffect(self._parse_short(signed=True))
                track.interpolate_type = InterpolationMode(
                    self._parse_short(signed=True)
                )
                track.keyframe_count = self._parse_short(signed=True)
                if (
                    track.keyframe_count > 0
                    and track.interpolate_type != InterpolationMode.CONSTANT
                ):
                    track.keyframe_offset = self._parse_int(signed=True)
                else:
                    track.constant = self._parse_float()

                motion.tracks.append(track)
                # print(f"\t{track}")

        # Parse keyframes
        keyframe_start_ofs = self._fl.tell()
        for motion in motions:
            for track in motion.tracks:
                name = ""
                if track.string_offset == -1:
                    name = f"{track.mode.name}_{track.value_index}"
                elif track.value_index > 0:
                    name = f"{self._parse_from_stringtable(track.string_offset)}_{track.value_index}"

                keyframes = []
                if (
                    track.keyframe_count > 0
                    and track.interpolate_type != InterpolationMode.CONSTANT
                ):
                    self._fl.seek(keyframe_start_ofs + track.keyframe_offset)
                    for _ in range(track.keyframe_count):
                        match track.interpolate_type:
                            case InterpolationMode.STEP | InterpolationMode.LINEAR:
                                keyframes.append(
                                    KeyFrame(self._parse_float(), self._parse_float())
                                )
                            case InterpolationMode.BITMAP:
                                keyframes.append(
                                    KeyFrame(
                                        self._parse_float(),
                                        self._parse_int(signed=True),
                                    )
                                )
                            case InterpolationMode.BEZIER:
                                keyframes.append(
                                    BezierKeyFrame(
                                        self._parse_float(),
                                        self._parse_float(),
                                        self._parse_float(),
                                        self._parse_float(),
                                    )
                                )
                            case _:
                                assert (
                                    False
                                ), f"Cannot parse interpolation mode {track.mode.name}"
                # print(f"\t{name} > {track.keyframe_count} vs {len(keyframes)}, {track}")

    def _parse_skeletons(self) -> list[SkeletonObject]:
        """Parses skeletons"""
        return self._parse_array(SkeletonParser, self._header.skeletons.length)

    def _parse_rigs(self):
        """Parses rigs/cenv"""
        rig_len = self._header.rigs.length
        print(f"Identified {rig_len} rig(s)")
        rig_headers: list[HSFRigHeader] = self._parse_array(RigHeaderParser, rig_len)
        start_ofs = self._fl.tell()

        envelopes: list[HSFEnvelope] = []
        for header in rig_headers:
            self._fl.seek(start_ofs + header.single_bind_offset, io.SEEK_SET)
            single_binds = self._parse_array(
                RiggingSingleBindParser, header.single_bind_count
            )

            self._fl.seek(start_ofs + header.double_bind_offset, io.SEEK_SET)
            double_binds = self._parse_array(
                RiggingDoubleBindParser, header.double_bind_count
            )

            self._fl.seek(start_ofs + header.multi_bind_offset, io.SEEK_SET)
            multi_binds = self._parse_array(
                RiggingMultiBindParser, header.multi_bind_count
            )

            envelopes.append(
                HSFEnvelope(
                    name=header.name,
                    single_binds=single_binds,
                    double_binds=double_binds,
                    multi_binds=multi_binds,
                    vertex_count=header.vertex_count,
                    copy_count=header.single_bind,
                )
            )

        # Parse weights corresponding to the binds
        weight_start_ofs = self._fl.tell()
        for cenv in envelopes:
            for bind in cenv.double_binds:
                self._fl.seek(weight_start_ofs + bind.weight_offset, io.SEEK_SET)
                bind.weights = self._parse_array(
                    RiggingDoubleWeightParser, bind.weight_count
                )
            for bind in cenv.multi_binds:
                self._fl.seek(weight_start_ofs + bind.weight_offset, io.SEEK_SET)
                bind.weights = self._parse_array(
                    RiggingMultiWeightParser, bind.weight_count
                )
        print(f"Envelopes: {len(envelopes)} > {envelopes}")
        return envelopes

    def _parse_textures(self):
        """Parse textures"""
        tex_len = self._header.textures.length
        pal_ofs = self._header.palettes.offset
        pal_len = self._header.palettes.length

        tex_infos: list[HSFTextureHeader] = self._parse_array(
            TextureHeaderParser, tex_len
        )
        ofs_post_tex = self._fl.tell()
        print(f"Identified {tex_len} texture(s)")

        self._fl.seek(pal_ofs, io.SEEK_SET)
        pal_infos: list[HSFPaletteHeader] = self._parse_array(
            PaletteHeaderParser, pal_len
        )
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

    def _parse_nodes(self) -> list[HSFNode]:
        """Parse the HSF-tree consisting of nodes"""
        node_len = self._header.nodes.length
        nodes: list[HSFNode] = []
        for i in range(node_len):
            # x = self._fl.tell()
            node = HSFNodeParser(self._fl, self._header).parse()
            node.index = i
            nodes.append(node)
            # print(
            #     f"Node parsed: ",
            #     i,
            #     node.type.name,
            #     node.name,
            #     node.attribute_index,
            #     node.material_data_ofs,
            # )
            # print(f"\t{self._attributes[node.attribute_index].}")
        return nodes

    def _setup_node_references(self, node: HSFNode):
        """
        Ties all node index references to related objects, such as
        the mesh-data, referenced replica-node, or parent/child relationships.

        Requires the following to be set:
        - `self._nodes`
        - `self._primitives`
        - `self._positions`
        - `self._normals`
        - `self._uvs`
        - `self._colors`
        - `self._envelopes`
        """
        if node.type == HSFNodeType.MESH:
            self._setup_mesh_references(node)

        # Setup node to replicate
        if node.replica_data and node.replica_data.replica_index != -1:
            node.replica_data.replica = self._nodes[node.replica_data.replica_index]

        if not node.has_hierarchy:
            # Cameras and Lights don't have parents/children
            self._non_hierarchy_nodes.append(node)
            return

        # Set easy access to parent
        if node.hierarchy_data:
            if node.hierarchy_data.parent_index != -1:
                node.hierarchy_data.parent = self._nodes[
                    node.hierarchy_data.parent_index
                ]
            else:
                self._root_node = node

            # Children are listed directly after the parent in the symbol indices
            for i in range(node.hierarchy_data.children_count):
                child_index = self._symbols[node.hierarchy_data.symbol_index + i]
                child = self._nodes[child_index]
                node.hierarchy_data.children.append(child)

    def _setup_mesh_references(self, node: HSFNode):
        """
        Ties all indices to the relevant data entries for the given mesh.
        E.g. primitive_index, position_index, etc.
        """
        assert node.mesh_data is not None
        # Primitives
        primitives_index = node.mesh_data.primitives_index
        assert (
            primitives_index != -1
        ), f"Expected primitives to be present for node {node}"
        primitives = self._primitives[primitives_index]

        # Positions
        positions_index = node.mesh_data.positions_index
        assert (
            positions_index != -1
        ), f"Expected positions to be present for node {node}"
        positions = self._positions[positions_index]

        # Normals
        nrm_index = node.mesh_data.nrm_index
        normal_indices_data = []
        if nrm_index != -1:
            normal_indices_data = self._normals[nrm_index].data

        # UV coords
        uv_index = node.mesh_data.uv_index
        uv_indices_data = []
        if uv_index != -1:
            uv_indices_data = self._uvs[uv_index].data

        # Vertex Colors
        color_index = node.mesh_data.color_index
        color_indices_data = []
        if color_index != -1:
            color_indices_data = self._colors[color_index].data

        # Attributes
        attribute_index = node.mesh_data.attribute_index
        attribute = None
        if attribute_index != -1:
            attribute = self._attributes[attribute_index]

        # Yet another sanity check. TODO: move
        expected_name = primitives.name
        for attributes in (positions,):
            assert (
                attributes.name == expected_name
            ), f"Encountered a name difference {attributes.name} vs {expected_name}"

        node.mesh_data.name = expected_name
        node.mesh_data.primitives = primitives.data
        node.mesh_data.positions = positions.data
        node.mesh_data.normals = normal_indices_data
        node.mesh_data.uvs = uv_indices_data
        node.mesh_data.colors = color_indices_data
        node.mesh_data.attribute = attribute

        for i in range(node.mesh_data.cenv_count):
            node.mesh_data.envelopes.append(
                self._envelopes[node.mesh_data.cenv_index + i]
            )
        import pprint

        print(f"Envelopes for '{node.mesh_data.name}' ({node.index}):")
        pprint.pprint(node.mesh_data.envelopes)
        print("----")

    def _verify_node_references(self, node: HSFNode):
        """Verifies that referenced indices are set up correctly. This is just a sanity check."""
        if node.hierarchy_data:
            # If a node has a parent, the node a child of its parent
            if node.hierarchy_data.parent is not None:
                assert (
                    node in node.hierarchy_data.parent.hierarchy_data.children
                ), "Node has a parent, but isn't a child of that parent"
            elif node.has_hierarchy:
                assert (
                    node == self._root_node
                ), f"Node ({node}) has no parent, but isn't the root node: {self._root_node})"
            # All children have their parent correctly set
            for child in node.hierarchy_data.children:
                assert (
                    child.hierarchy_data.parent == node
                ), "Node has children, but isn't a parent for one of them"
            # Non-hierarchy nodes
            if not node.has_hierarchy:
                assert (
                    node.hierarchy_data.parent is None
                ), "Node is not hierarchical but has a parent"
                assert (
                    not node.hierarchy_data.children
                ), "Node is not hierarchical but has children"
        # Replicas
        if node.replica_data and node.replica_data.replica:
            assert (
                node.replica_data.replica.type == HSFNodeType.NULL1
            ), "Replica node replicates a non-NULL1 node"
