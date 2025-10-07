import io
import pprint

from nokonoko_estate.formats.enums import CombinerBlend, WrapMode
from nokonoko_estate.formats.formats import (
    AttrTransform,
    AttributeHeader,
    HSFCameraNodeData,
    HSFHeader,
    HSFHierarchyNodeData,
    HSFLightNodeData,
    HSFLightType,
    HSFMeshNodeData,
    HSFNode,
    HSFNodeType,
    HSFReplicaNodeData,
    HSFRigHeader,
    LightingChannelFlags,
    MaterialObject,
    AttributeObject,
    HSFMotionDataHeader,
    NodeTransform,
    HSFPaletteHeader,
    HSFTextureHeader,
    RiggingDoubleBind,
    RiggingDoubleWeight,
    RiggingMultiBind,
    RiggingMultiWeight,
    RiggingSingleBind,
    SkeletonObject,
    Vertex,
)
from nokonoko_estate.parsers.base import HSFParserBase


class HSFHeaderParser(HSFParserBase[HSFHeader]):
    """Parses a HSFV037 header"""

    _data_type = HSFHeader

    def parse(self) -> HSFHeader:
        magic = self._fl.read(0x08)
        if magic != b"HSFV037\x00":
            self._logger.error("Invalid file magic")
            raise ValueError("Invalid file magic encountered!")

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

        # Bones/nodes tie everything together
        header.nodes.offset = self._parse_int()
        header.nodes.length = self._parse_int()

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

        self._logger.debug("Header:\n" + pprint.pformat(header))
        return header


class HSFHierarchyNodeDataParser(HSFParserBase[HSFHierarchyNodeData]):
    """Parses the hierarchy-data of a HSF-node"""

    def parse(self) -> HSFHierarchyNodeData:
        data = HSFHierarchyNodeData()
        data.parent_index = self._parse_index()
        data.children_count = self._parse_int()
        data.symbol_index = self._parse_index()
        data.base_transform = NodeTransform(
            (self._parse_float(), self._parse_float(), self._parse_float()),
            (self._parse_float(), self._parse_float(), self._parse_float()),
            (self._parse_float(), self._parse_float(), self._parse_float()),
        )
        data.current_transform = NodeTransform(
            (self._parse_float(), self._parse_float(), self._parse_float()),
            (self._parse_float(), self._parse_float(), self._parse_float()),
            (self._parse_float(), self._parse_float(), self._parse_float()),
        )
        return data


class HSFReplicaNodeDataParser(HSFParserBase[HSFReplicaNodeData]):
    """Parses the replica-data of a HSF-node"""

    def parse(self) -> HSFReplicaNodeData:
        data = HSFReplicaNodeData()
        data.replica_index = self._parse_int()
        return data


class HSFMeshNodeDataParser(HSFParserBase[HSFMeshNodeData]):
    """Parses the mesh-data of a HSF-node"""

    def parse(self) -> HSFMeshNodeData:
        data = HSFMeshNodeData()
        data.cull_box_min = (
            self._parse_float(),
            self._parse_float(),
            self._parse_float(),
        )
        data.cull_box_max = (
            self._parse_float(),
            self._parse_float(),
            self._parse_float(),
        )
        data.base_morph = self._parse_float()
        data.morph_weights = self._fl.read(0x20 * 4)

        data.unk_index = self._parse_index()
        data.primitives_index = self._parse_index()
        data.positions_index = self._parse_index()
        data.nrm_index = self._parse_index()
        data.color_index = self._parse_index()
        data.uv_index = self._parse_index()

        data.material_data_ofs = self._parse_int()
        data.attribute_index = self._parse_index()  # Materials
        data.unk02 = self._parse_byte()  # byte
        data.unk03 = self._parse_byte()  # byte
        data.shape_type = self._parse_byte()  # byte
        data.unk04 = self._parse_byte()  # byte
        data.shape_count = self._parse_int()
        data.shape_symbol_index = self._parse_index()
        data.cluster_count = self._parse_int()
        data.cluster_symbol_index = self._parse_index()
        data.cenv_count = self._parse_int()
        data.cenv_index = self._parse_index()
        data.cluster_position_ofs = self._parse_int()
        data.cluster_nrm_ofs = self._parse_int()
        return data


class HSFLightNodeDataParser(HSFParserBase[HSFLightNodeData]):
    """Parses the light-data of a HSF-node"""

    def parse(self) -> HSFLightNodeData:
        data = HSFLightNodeData()
        data.position = (self._parse_float(), self._parse_float(), self._parse_float())
        data.target = (self._parse_float(), self._parse_float(), self._parse_float())
        data.light_type = HSFLightType(self._parse_byte())
        data.r = self._parse_byte()
        data.g = self._parse_byte()
        data.b = self._parse_byte()
        data.unk2c = self._parse_float()
        data.ref_distance = self._parse_float()
        data.ref_brightness = self._parse_float()
        data.cutoff = self._parse_float()
        return data


class HSFCameraNodeDataParser(HSFParserBase[HSFCameraNodeData]):
    """Parses the camera-data of a HSF-node"""

    def parse(self) -> HSFCameraNodeData:
        data = HSFCameraNodeData()
        data.target = (self._parse_float(), self._parse_float(), self._parse_float())
        data.position = (self._parse_float(), self._parse_float(), self._parse_float())
        data.aspect_ratio = self._parse_float()
        data.fov = self._parse_float()
        data.near = self._parse_float()
        data.far = self._parse_float()
        return data


class HSFNodeParser(HSFParserBase[HSFNode]):
    """Parses an HSF-node"""

    def parse(self) -> HSFNode:
        start = self._fl.tell()
        node = HSFNode()
        str_ofs = self._parse_int()
        node.name = self._parse_from_stringtable(str_ofs, -1)
        node.type = HSFNodeType(self._parse_int())
        node.const_data_ofs = self._parse_int()
        node.render_flags = self._parse_int()

        if node.type in (HSFNodeType.NULL1, HSFNodeType.MESH, HSFNodeType.REPLICA):
            h_parser = HSFHierarchyNodeDataParser(self._fl, self._header)
            node.hierarchy_data = h_parser.parse()

        match node.type:
            case HSFNodeType.NULL1:
                # The remainder of the data is junk data. This data was left over from the previous node
                #   in the node list when the HSF-file was created. Skip over all this junk.
                # m_parser = HSFMeshNodeDataParser(self._fl, self._header)
                # node.mesh_data = m_parser.parse()
                self._fl.seek(start + 0x144, io.SEEK_SET)
            case HSFNodeType.MESH:
                m_parser = HSFMeshNodeDataParser(self._fl, self._header)
                node.mesh_data = m_parser.parse()
            case HSFNodeType.REPLICA:
                r_parser = HSFReplicaNodeDataParser(self._fl, self._header)
                node.replica_data = r_parser.parse()
                self._fl.seek(start + 0x144, io.SEEK_SET)
                assert (
                    self._fl.tell() == start + 0x144
                ), "Data reader is in the incorrect position!"
            case HSFNodeType.LIGHT:
                r_parser = HSFLightNodeDataParser(self._fl, self._header)
                node.light_data = r_parser.parse()
                self._fl.seek(start + 0x144, io.SEEK_SET)
            case HSFNodeType.CAMERA:
                r_parser = HSFCameraNodeDataParser(self._fl, self._header)
                node.camera_data = r_parser.parse()
                self._fl.seek(start + 0x144, io.SEEK_SET)
            case _:
                raise ValueError(f"Cannot parse {node.type}-node: {node}")
        return node


class AttributeHeaderParser(HSFParserBase[AttributeHeader]):
    """Parses material attribute headers"""

    _data_type = AttributeHeader
    struct_formatting = ">iii"


class VertexParser(HSFParserBase[Vertex]):
    """Parses Vertices"""

    _data_type = Vertex
    struct_formatting = ">hhhh"


class AttributeParser(HSFParserBase[AttributeObject]):
    """Parses material attributes"""

    _data_type = AttributeObject

    def parse(self) -> AttributeObject:
        str_ofs = self._parse_index()
        name = None
        if str_ofs != -1:
            name = self._parse_from_stringtable(str_ofs, -1)
        obj = AttributeObject(name)

        obj.tex_animation_offset = self._parse_index()
        obj.unk_1 = self._parse_short()
        obj.blend_flag = CombinerBlend(self._parse_index(0x1))

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

        obj.wrap_s = WrapMode(self._parse_int(signed=True))
        obj.wrap_t = WrapMode(self._parse_int(signed=True))

        obj.unk_10 = self._parse_int()
        obj.unk_11 = self._parse_int()
        obj.unk_12 = self._parse_int()

        obj.mipmap_max_lod = self._parse_int(signed=True)
        obj.texture_flags = self._parse_int()
        obj.texture_index = self._parse_index()

        return obj


class MaterialObjectParser(HSFParserBase[MaterialObject]):
    """Parses materials"""

    _data_type = MaterialObject

    def parse(self) -> MaterialObject:
        str_ofs = self._parse_index()
        name = None
        if str_ofs != -1:
            name = self._parse_from_stringtable(str_ofs, -1)
        mat = MaterialObject(name)
        mat.unk01 = self._parse_int()
        mat.alt_flags = self._parse_short()
        mat.vertex_mode = LightingChannelFlags(self._parse_byte())
        mat.ambient_color = (self._parse_byte(), self._parse_byte(), self._parse_byte())
        mat.material_color = (
            self._parse_byte(),
            self._parse_byte(),
            self._parse_byte(),
        )
        mat.shadow_color = (self._parse_byte(), self._parse_byte(), self._parse_byte())
        mat.hi_lite_scale = self._parse_float()
        mat.unk02 = self._parse_float()
        mat.transparency_inverted = self._parse_float()
        mat.unk03 = self._parse_float()
        mat.unk04 = self._parse_float()
        mat.reflection_intensity = self._parse_float()
        mat.unk05 = self._parse_float()
        mat.material_flags = self._parse_int()
        mat.texture_count = self._parse_int()
        mat.attribute_index = self._parse_int()

        return mat


class SkeletonParser(HSFParserBase[SkeletonObject]):
    """Parses skeletons"""

    _data_type = SkeletonObject

    def parse(self):
        data = SkeletonObject()
        data.name = self._parse_from_stringtable(self._parse_int())
        data.transform = NodeTransform(
            (self._parse_float(), self._parse_float(), self._parse_float()),
            (self._parse_float(), self._parse_float(), self._parse_float()),
            (self._parse_float(), self._parse_float(), self._parse_float()),
        )
        return data


class RigHeaderParser(HSFParserBase[HSFRigHeader]):
    """Parses rigs/cenv"""

    _data_type = HSFRigHeader
    struct_formatting = ">IIIIIIIII"


class RiggingSingleBindParser(HSFParserBase[RiggingSingleBind]):
    """Parses RiggingSingleBind"""

    _data_type = RiggingSingleBind
    struct_formatting = ">ihhhh"


class RiggingDoubleBindParser(HSFParserBase[RiggingDoubleBind]):
    """Parses RiggingDoubleBind"""

    _data_type = RiggingDoubleBind
    struct_formatting = ">iiii"


class RiggingMultiBindParser(HSFParserBase[RiggingMultiBind]):
    """Parses RiggingMultiBind"""

    _data_type = RiggingMultiBind
    struct_formatting = ">ihhhhi"


class RiggingDoubleWeightParser(HSFParserBase[RiggingDoubleWeight]):
    """Parses RiggingDoubleWeight"""

    _data_type = RiggingDoubleWeight
    struct_formatting = ">fhhhh"


class RiggingMultiWeightParser(HSFParserBase[RiggingMultiWeight]):
    """Parses RiggingMultiWeight"""

    _data_type = RiggingMultiWeight
    struct_formatting = ">if"


class TextureHeaderParser(HSFParserBase[HSFTextureHeader]):
    """Parses texture headers"""

    _data_type = HSFTextureHeader
    struct_formatting = ">IIBBHHHIiII"


class PaletteHeaderParser(HSFParserBase[HSFPaletteHeader]):
    """Parses palette headers"""

    _data_type = HSFPaletteHeader
    struct_formatting = ">IiiI"


class MotionDataHeaderParser(HSFParserBase[HSFMotionDataHeader]):
    """Parses animation headers"""

    _data_type = HSFMotionDataHeader
    struct_formatting = ">IIIf"
