from collections import defaultdict
from datetime import datetime
import logging
import pprint
from typing import Literal
import xml.etree.ElementTree as ET

from PIL import Image

from nokonoko_estate.formats.enums import WrapMode
from nokonoko_estate.formats.formats import (
    HSFFile,
    AttributeObject,
    HSFMeshNodeData,
    HSFNode,
    HSFNodeType,
    PrimitiveObject,
    Vertex,
)
from nokonoko_estate.formats.matrix import TransformationMatrix

ColladaTriangle = tuple[Vertex, Vertex, Vertex]
ColladaPolygon = tuple[Vertex, Vertex, Vertex, Vertex]
ColladaSetIdx = tuple[
    int, bool, bool, bool
]  # attribute_index, has_normals, has_uvs, has_colors, ...


class HSFFileDAESerializer:
    """Serializes HSF-data into a DAE-file"""

    def __init__(self, data: HSFFile, output_filepath: str):
        self._data = data
        self.output_path = output_filepath
        self._logger = logging.getLogger(self.__class__.__qualname__)

    def serialize(self):
        """Serialize the HSF-file (`self.data`) and output it to `self.output_filepath`"""
        root = ET.Element("COLLADA")
        root.set("xmlns", "http://www.collada.org/2005/11/COLLADASchema")
        root.set("version", "1.4.1")
        asset = ET.SubElement(root, "asset")
        contributor = ET.SubElement(asset, "contributor")
        ET.SubElement(contributor, "author_website").text = (
            "https://github.com/Scutlet/Nokonoko-Estate-Exporter"
        )
        author = ET.SubElement(contributor, "authoring_tool")
        author.text = "Nokonoko Estate Exporter"
        created = ET.SubElement(asset, "created")
        created.text = datetime.now().isoformat(timespec="seconds")
        up_axis = ET.SubElement(asset, "up_axis")
        up_axis.text = "Y_UP"

        # Images
        library_images = ET.SubElement(root, "library_images")
        for i, (name, texture) in enumerate(self._data.textures):
            library_images.append(self.serialize_image(name, texture, i))

        # Materials & Effects
        # TODO: Fix materialObjects vs AttributeObject
        library_materials = ET.SubElement(root, "library_materials")
        library_effects = ET.SubElement(root, "library_effects")
        for i, mat in enumerate(self._data.attributes):
            library_materials.append(self.serialize_material(mat, i))
            library_effects.append(self.serialize_effects(mat, i))

        # Geometry & controller
        geometries = ET.SubElement(root, "library_geometries")
        controllers = ET.SubElement(root, "library_controllers")
        for i, node in enumerate(
            filter(lambda node: node.type == HSFNodeType.MESH, self._data.nodes)
        ):
            geometries.append(self.serialize_geometry(node))
            controllers.append(self.serialize_controller(node))

        # Visual scenes
        visual_scenes = ET.SubElement(root, "library_visual_scenes")
        visual_scene = ET.SubElement(
            visual_scenes, "visual_scene", id="Scene", name="Scene"
        )

        armature_root = ET.SubElement(
            visual_scene, "node", id="Armature", name="Armature", type="NODE"
        )
        collada_nodes: dict[int, ET.Element] = [None] * len(self._data.nodes)
        for node, _ in self._data.root_node.dfs():
            match node.type:
                case HSFNodeType.MESH:
                    collada_nodes[node.index] = self.serialize_visual_scene_mesh(node)
                    armature_root.append(collada_nodes[node.index])
                    # if node.hierarchy_data.parent:
                    #     collada_nodes[node.hierarchy_data.parent.index].append(
                    #         collada_nodes[node.index]
                    #     )
                case HSFNodeType.REPLICA:
                    # TODO
                    pass
                    # for e in self.serialize_visual_scene_replica(node):
                    #     visual_scene.append(e)
                case HSFNodeType.NULL1:
                    collada_nodes[node.index] = self.serialize_visual_scene_joint(node)
                    if node.hierarchy_data.parent:
                        collada_nodes[node.hierarchy_data.parent.index].append(
                            collada_nodes[node.index]
                        )
                case _:
                    # For all other nodes, do nothing
                    continue
        armature_root.append(collada_nodes[self._data.root_node.index])

        # for i, node in enumerate(self._data.nodes):
        #     # Add all meshes to the scene
        #     match node.type:
        #         case HSFNodeType.MESH:
        #             visual_scene.append(self.serialize_visual_scene_mesh(node))
        #         case HSFNodeType.REPLICA:
        #             for e in self.serialize_visual_scene_replica(node):
        #                 visual_scene.append(e)
        #         case _:
        #             # For all other nodes, do nothing
        #             continue

        # Scene
        scene = ET.SubElement(root, "scene")
        instance_visual_scene = ET.SubElement(
            scene, "instance_visual_scene", url="#Scene"
        )

        ET.indent(root, space=" ", level=0)
        tree = ET.ElementTree(root)
        tree.write(self.output_path, encoding="utf-8", xml_declaration=True)

    def serialize_image(
        self, name: str, texture: Image.Image, index: int
    ) -> ET.Element:
        """Serializes textures into <image> nodes"""
        image = ET.Element(
            "image",
            id=f"texture_{index:03}",
            name=name,
            width=str(texture.width),
            height=str(texture.height),
        )
        init = ET.SubElement(image, "init_from")
        init.text = f"images/{name}.png"
        return image

    def serialize_material(self, material: AttributeObject, index: int) -> ET.Element:
        """Serialize <material> nodes. References <effects> (texture info)"""
        mat = ET.Element("material", id=f"material_{index:03}")
        ET.SubElement(mat, "instance_effect", url=f"#Effect_material_{index:03}")
        return mat

    def serialize_effects(self, material: AttributeObject, index: int) -> ET.Element:
        """Serialize <effect> nodes to list texture information (filename, format, UV-wrap, etc.)"""
        effect = ET.Element("effect", id=f"Effect_material_{index:03}")
        profile = ET.SubElement(effect, "profile_COMMON")
        surface_param = ET.SubElement(
            profile, "newparam", sid=f"surface_material_{index:03}"
        )
        surface = ET.SubElement(surface_param, "surface", type="2D")
        ET.SubElement(surface, "init_from").text = (
            f"texture_{material.texture_index:03}"
        )
        ET.SubElement(surface, "format").text = f"A8R8G8B8"

        sampler_param = ET.SubElement(
            profile, "newparam", sid=f"sampler_material_{index:03}"
        )
        sampler2d = ET.SubElement(sampler_param, "sampler2D")
        ET.SubElement(sampler2d, "source").text = f"surface_material_{index:03}"

        collada_wrap_modes = {
            WrapMode.REPEAT: "WRAP",
            WrapMode.MIRROR: "MIRROR",
            WrapMode.CLAMP: "CLAMP",
        }
        ET.SubElement(sampler2d, "wrap_s").text = collada_wrap_modes[material.wrap_s]
        ET.SubElement(sampler2d, "wrap_t").text = collada_wrap_modes[material.wrap_t]
        ET.SubElement(sampler2d, "mipmap_maxlevel").text = str(material.mipmap_max_lod)

        technique = ET.SubElement(profile, "technique", sid="common")
        lambert = ET.SubElement(technique, "lambert")
        diffuse = ET.SubElement(lambert, "diffuse")
        ET.SubElement(
            diffuse,
            "texture",
            texture=f"sampler_material_{index:03}",
            texcoord="",  # TODO: texcoord
        )
        if material.alpha_flag:
            # NB: Goes unused after Blender 2.79b
            # https://projects.blender.org/blender/blender/issues/98920
            transparent = ET.SubElement(lambert, "transparent")
            ET.SubElement(
                transparent,
                "texture",
                texture=f"sampler_material_{index:03}",
                texcoord="",
            )
        # Prevent Blender from complaining
        ior = ET.SubElement(
            ET.SubElement(lambert, "index_of_refraction"), "float", sid="ior"
        )
        ior.text = "1.45"

        return effect

    def serialize_geometry(self, node: HSFNode) -> ET.Element:
        """
        Serializes a single <geometry> node. This basically represents a single mesh,
        which can be instantiated multiple times. E.g. for REPLICA nodes
        """
        assert node.mesh_data is not None
        uid = f"{node.mesh_data.name}__{node.index}"

        geometry = ET.Element("geometry", id=f"{uid}-mesh", name=uid)
        mesh = ET.SubElement(geometry, "mesh")
        mesh.append(self.serialize_positions(node.mesh_data, node.index))
        # Normals, UVs, colors may not exist. Only serialize them if they do
        if node.mesh_data.normals:
            mesh.append(self.serialize_normals(node.mesh_data, node.index))
        if node.mesh_data.uvs:
            mesh.append(self.serialize_uvs(node.mesh_data, node.index))
        if node.mesh_data.colors:
            mesh.append(self.serialize_colors(node.mesh_data, node.index))

        vertices = ET.SubElement(mesh, "vertices", id=f"{uid}-vertex")
        ET.SubElement(vertices, "input", semantic="POSITION", source=f"#{uid}-position")

        # Group primitives by material and whether they have UVs/colors/normals
        triangle_dict: dict[ColladaSetIdx, list[ColladaTriangle]] = defaultdict(list)
        polylist_dict: dict[ColladaSetIdx, list[ColladaPolygon]] = defaultdict(list)
        self._generate_vertices_from_primitives(
            node.mesh_data.primitives, triangle_dict, polylist_dict
        )

        self._sanity_check_collada_sets(node.mesh_data, triangle_dict)
        self._sanity_check_collada_sets(node.mesh_data, polylist_dict)

        # Define quads
        for elem in self._serialize_primitive_dict(
            "polylist", polylist_dict, uid, include_vcount=True
        ):
            mesh.append(elem)

        # Define triangles
        for elem in self._serialize_primitive_dict("triangles", triangle_dict, uid):
            mesh.append(elem)
        return geometry

    def serialize_controller(self, node: HSFNode) -> ET.Element:
        """
        Serializes a single <controller> node. Used for assigning weights to vertices
        """
        assert node.mesh_data is not None
        assert node.hierarchy_data is not None

        uid = f"{node.mesh_data.name}__{node.index}"
        armature_uid = f"Armature_{uid}-skin"
        controller = ET.Element(
            "controller", id=armature_uid, name=f"Armature {node.name}"
        )
        skin = ET.SubElement(controller, "skin", source=f"#{uid}-mesh")

        # Offset into world space when in the rest pose
        ET.SubElement(skin, "bind_shape_matrix").text = (
            self._serialize_transformation_matrix(node.hierarchy_data.world_transform())
        )

        # ============================================================
        # Determine which bones need to be referenced
        if not node.mesh_data.envelopes:
            return controller
        elif len(node.mesh_data.envelopes) > 1:
            self._logger.warning(
                f"For mesh {node.name}, multiple envelopes were encountered. Only the first will be used! Envelopes: \n{pprint.pformat(node.mesh_data.envelopes)}"
            )

        env = node.mesh_data.envelopes[0]
        # Weights listed per vertex, such that weights[positionIdx] = [(boneIdx, weight), ...]
        vertex_weights: list[list[tuple[int, int]]] = [
            [] for _ in node.mesh_data.positions
        ]

        if env.copy_count > 0:
            if env.single_binds or env.double_binds or env.multi_binds:
                self._logger.warning(
                    f"For mesh {node.name} ({node.index}), encountered an envelope with copy_count > 0 and binds: \n{pprint.pformat(env)}"
                )
            if node.hierarchy_data.parent is None:
                self._logger.warning(
                    f"for mesh {node.name} ({node.index}), has copy_count > 0, but does not have a parent: \n{pprint.pformat(env)}"
                )

        # Parse weights for each vertex
        # TODO: normal_index/normal_count?
        for i, _ in enumerate(node.mesh_data.positions):
            # Parse single binds (weight = 1 for the referenced bone)
            for bind in env.single_binds:
                if (
                    i >= bind.position_index
                    and i < bind.position_index + bind.position_count
                ):
                    vertex_weights[i].append((bind.node_index, 1))

            # Double binds (weight w specified for the referenced bone; weight 1 - w for the other referenced bone)
            for bind in env.double_binds:
                for weight in bind.weights:
                    if (
                        i >= weight.position_index
                        and i < weight.position_index + weight.position_count
                    ):
                        vertex_weights[i].append((bind.node_index_1, weight.weight))
                        vertex_weights[i].append((bind.node_index_2, 1 - weight.weight))

            # Multi binds (multiple weights specified for each position. E.g. w1, w2, w3 (each sum to 1))
            for bind in env.multi_binds:
                if (
                    i >= bind.position_index
                    and i < bind.position_index + bind.position_count
                ):
                    for weight in bind.weights:
                        vertex_weights[i].append((weight.node_index, weight.weight))

            # Assume that, if copy_count is set, the mesh is fully rigged to its parent node
            if node.hierarchy_data.parent:
                if i < env.copy_count:
                    vertex_weights[i].append((node.hierarchy_data.parent_index, 1))

        res_bones: list[HSFNode] = []
        res_weights: list[str] = []
        # Indices into result arrays to flatten identical bone uids and weights
        #   res_bones[bones_dict[<bone_index>]] = <bone_uid>
        #   res_weights[weights_dict[<weight>]] = <weight-6-decimal-places>
        bones_dict: dict[int, int] = {}
        weights_dict: dict[str, int] = {}

        # Write results dict
        for i, weights in enumerate(vertex_weights):
            for node_index, weight in weights:
                weight = f"{weight:f}"
                if node_index not in bones_dict:
                    n = self._data.nodes[node_index]
                    res_bones.append(n)
                    bones_dict[node_index] = len(res_bones) - 1
                if weight not in weights_dict:
                    res_weights.append(weight)
                    weights_dict[weight] = len(res_weights) - 1

        # Joints (bones)
        source = ET.SubElement(skin, "source", id=f"{uid}-skin-joints")
        name_arr = ET.SubElement(
            source,
            "Name_array",
            id=f"{armature_uid}-joints-array",
            count=str(len(res_bones)),
        )
        name_arr.text = " ".join(map(lambda n: f"{n.name}__{n.index}", res_bones))
        technique = ET.SubElement(source, "technique_common")
        accessor = ET.SubElement(
            technique,
            "accessor",
            source=f"#{armature_uid}-joints-array",
            count=str(len(res_bones)),
            stride="1",
        )
        ET.SubElement(accessor, "param", name="JOINT", type="name")

        # Binds
        source = self.serialize_vertex_data_array(
            [
                (node.hierarchy_data.inverse_bind_matrix(bone).round()).as_raw()
                for bone in res_bones
            ],
            f"{uid}-skin-bind_poses",
        )
        skin.append(source)
        technique = ET.SubElement(source, "technique_common")
        accessor = ET.SubElement(
            technique,
            "accessor",
            source=f"#{uid}-skin-bind_poses-array",
            count=str(len(res_bones)),
            stride="16",
        )
        ET.SubElement(accessor, "param", name="TRANSFORM", type="float4x4")

        # Weights
        source = ET.SubElement(skin, "source", id=f"{uid}-skin-weights")
        float_arr = ET.SubElement(
            source,
            "float_array",
            id=f"{armature_uid}-skin-weights-array",
            count=str(len(res_weights)),
        )
        float_arr.text = " ".join(res_weights)
        technique = ET.SubElement(source, "technique_common")
        accessor = ET.SubElement(
            technique,
            "accessor",
            source=f"#{uid}-skin-weights",
            count=str(len(res_weights)),
            stride="1",
        )
        ET.SubElement(accessor, "param", name="WEIGHT", type="float")

        # Joints
        joints = ET.SubElement(skin, "joints")
        ET.SubElement(joints, "input", semantic="JOINT", source=f"#{uid}-skin-joints")
        ET.SubElement(
            joints,
            "input",
            semantic="INV_BIND_MATRIX",
            source=f"#{uid}-skin-bind_poses",
        )

        # Vertex weights
        vcount: list[str] = []
        v: list[tuple[str, str]] = []

        for i, pos_weights in enumerate(vertex_weights):
            weight_sum = sum(map(lambda x: x[1], pos_weights))
            if weight_sum not in (0, 1):
                self._logger.warning(
                    f"Weight sum in {node.name} ({node.index}) for position {i} is {weight_sum}. Should be 1.0"
                )
            vcount.append(str(len(pos_weights)))
            for bone_idx, w in pos_weights:
                v.append(str(bones_dict[bone_idx]))
                v.append(str(weights_dict[f"{w:f}"]))

        xml_v_weights = ET.Element("vertex_weights", count=str(len(vcount)))
        skin.append(xml_v_weights)
        ET.SubElement(
            xml_v_weights,
            "input",
            semantic="JOINT",
            source=f"#{uid}-skin-joints",
            offset="0",
        )
        ET.SubElement(
            xml_v_weights,
            "input",
            semantic="WEIGHT",
            source=f"#{uid}-skin-weights",
            offset="1",
        )
        # The amount of weights the nth vertex has (in each mesh's <vertices> element). All weights should add up to 1
        ET.SubElement(xml_v_weights, "vcount").text = " ".join(vcount)
        ET.SubElement(xml_v_weights, "v").text = " ".join(v)

        return controller

    def _generate_vertices_from_primitives(
        self,
        primitives: list[PrimitiveObject],
        triangle_dict: dict[ColladaSetIdx, list[ColladaTriangle]],
        polylist_dict: dict[ColladaSetIdx, list[ColladaPolygon]],
    ) -> None:
        """
        Generate sets of matching primitives. I.e. matching material, and whether it has colors/uvs/normals.
        Each set is exported to its own <polylist> or <triangle> element later on
        """
        for primitive in primitives:
            attribute_index = -1
            if primitive.material_index != -1:
                attribute_index = self._data.materials[
                    primitive.material_index
                ].attribute_index

            collada_set_idx: ColladaSetIdx = (
                attribute_index,
                primitive.vertices[0].normal_index != -1,
                primitive.vertices[0].uv_index != -1,
                primitive.vertices[0].color_index != -1,
            )

            match primitive.primitive_type:
                case PrimitiveObject.PrimitiveType.PRIMITIVE_TRIANGLE:
                    triangle_dict[collada_set_idx].append(
                        self.primitive_triangle_to_collada(primitive)
                    )
                case PrimitiveObject.PrimitiveType.PRIMITIVE_QUAD:
                    polylist_dict[collada_set_idx].append(
                        self.primitive_quad_to_collada(primitive)
                    )
                case PrimitiveObject.PrimitiveType.PRIMITIVE_TRIANGLE_STRIP:
                    # Blender does not support COLLADA's <tristrips>-element. We'll include them as plain old triangles.
                    triangle_dict[
                        collada_set_idx
                    ] += self.primtive_triangle_strip_to_collada(primitive)
                case _:
                    raise NotImplementedError(
                        f"Cannot serialize {primitive.primitive_type.name}"
                    )

    def _sanity_check_collada_sets(
        self,
        mesh_data: HSFMeshNodeData,
        prim_dict: dict[ColladaSetIdx, list[list[Vertex]]],
    ) -> None:
        """TODO"""
        # TODO: Include more general index validity checking in the parser instead of the serializer
        # Check if mesh_obj.uvs is empty, but uv_data was defined!
        if not mesh_data.uvs:
            for collada_set_idx, primitive_vertices in prim_dict.items():
                attribute_index = collada_set_idx[0]
                for vertices in primitive_vertices:
                    if vertices[0].uv_index != -1:
                        self._logger.warning(
                            f"WARN: Mesh {mesh_data.name} has no UV's. Attribute_index {attribute_index} contains a vertex with a uv-index ({vertices[0].uv_index}) defined! UV-index will be ignored!"
                        )

        for collada_set_idx, primitive_vertices in prim_dict.items():
            attribute_index = collada_set_idx[0]
            has_prim_with_uvs = False
            has_prim_without_uvs = False
            for vertices in primitive_vertices:
                if vertices[0].uv_index == -1:
                    has_prim_without_uvs = True
                else:
                    has_prim_with_uvs = True
            if has_prim_with_uvs and has_prim_without_uvs:
                self._logger.warning(
                    f"Mesh {mesh_data.name} with Attribute_index {attribute_index} contains primitives with and without UV-indices."
                )

        # TODO: Check if, within a single dictionary item, there are vertices with AND without uv-indices. These should never mix 'n match!

    def _serialize_vertex(
        self,
        vertex: Vertex,
        include_normals: bool,
        include_uvs: bool,
        include_colors: bool,
    ) -> str:
        """Serializes a vertex to COLLADA format"""
        v = str(vertex.position_index)
        if include_normals:
            v += " " + str(vertex.normal_index)
        if include_uvs:
            v += " " + str(vertex.uv_index)
        if include_colors:
            v += " " + str(vertex.color_index)
        return v

    def _serialize_primitive_dict(
        self,
        name: Literal["triangles", "polylist"],
        prim_dict: dict[ColladaSetIdx, list[list[Vertex]]],
        uid: str,
        include_vcount=False,
    ) -> list[ET.Element]:
        """
        Serializes sets of primitives to a series of <triangle> or <polylist> elements.
        """
        xml_elems = []
        for (
            attribute_index,
            has_normals,
            has_uvs,
            has_colors,
        ), primitive_vertices in prim_dict.items():
            polys = ET.Element(
                name,
                count=str(len(primitive_vertices)),
            )
            if attribute_index != -1:
                polys.attrib["material"] = f"material_{attribute_index:03}"
            xml_elems.append(polys)

            for input in self._serialize_inputs(
                uid,
                include_normals=primitive_vertices[0][0].normal_index != -1,
                include_uvs=primitive_vertices[0][0].uv_index != -1,
                include_colors=primitive_vertices[0][0].color_index != -1,
            ):
                polys.append(input)

            if include_vcount:
                vcount = ET.SubElement(polys, "vcount")
                vcount.text = " ".join(
                    [str(len(vertices)) for vertices in primitive_vertices]
                )

            p_elem = ET.SubElement(polys, "p")
            p_elem.text = " ".join(
                [
                    " ".join(
                        [
                            self._serialize_vertex(v, has_normals, has_uvs, has_colors)
                            for v in vertices
                        ]
                    )
                    for vertices in primitive_vertices
                ]
            )

        return xml_elems

    def _serialize_inputs(
        self,
        mesh_obj_uid: str,
        include_normals=True,
        include_uvs=True,
        include_colors=True,
    ) -> list[ET.Element]:
        """Serializes <input> elements. These are used by geometry-elements to correctly index into the right data"""
        offset = 0
        inputs = [
            ET.Element(
                "input",
                semantic="VERTEX",
                source=f"#{mesh_obj_uid}-vertex",
                offset=str(offset),
            )
        ]
        # TODO: Are there ever elements without normals?
        if include_normals:
            offset += 1
            inputs.append(
                ET.Element(
                    "input",
                    semantic="NORMAL",
                    source=f"#{mesh_obj_uid}-normals",
                    offset=str(offset),
                )
            )
        else:
            self._logger.warning(f"Mesh {mesh_obj_uid} does NOT have normals defined!")
        if include_uvs:
            offset += 1
            inputs.append(
                ET.Element(
                    "input",
                    semantic="TEXCOORD",
                    source=f"#{mesh_obj_uid}-texcoord",
                    offset=str(offset),
                )
            )
        if include_colors:
            offset += 1
            inputs.append(
                ET.Element(
                    "input",
                    semantic="COLOR",
                    source=f"#{mesh_obj_uid}-colors",
                    offset=str(offset),
                )
            )
        return inputs

    def primitive_triangle_to_collada(
        self, primitive: PrimitiveObject
    ) -> ColladaTriangle:
        """Converts a primitive triangle to a triangle in COLLADA-format (taking care of the winding order)"""
        assert (
            primitive.primitive_type == PrimitiveObject.PrimitiveType.PRIMITIVE_TRIANGLE
        )

        # The fourth primitive is a dummy and always references the first element in each array (position, normal, color, uv)
        return (
            primitive.vertices[0],
            primitive.vertices[1],
            primitive.vertices[2],
        )

    def primitive_quad_to_collada(self, primitive: PrimitiveObject) -> ColladaPolygon:
        """Converts a primitive quad to a polygon in COLLADA format (taking care of the winding order)"""
        assert primitive.primitive_type == PrimitiveObject.PrimitiveType.PRIMITIVE_QUAD
        # The winding order of vertices produced is counter-clockwise and describes the front side of each polygon
        # Order in HSF-file: 0 1 3 2
        return (
            primitive.vertices[0],
            primitive.vertices[1],
            primitive.vertices[3],
            primitive.vertices[2],
        )

    def primtive_triangle_strip_to_collada(
        self, primitive: PrimitiveObject
    ) -> list[ColladaTriangle]:
        """Converts a primitive triangle strip to a series of COLLADA-triangles (taking care of the winding order)"""
        assert (
            primitive.primitive_type
            == PrimitiveObject.PrimitiveType.PRIMITIVE_TRIANGLE_STRIP
        )
        triangles = []
        for i in range(len(primitive.vertices) - 2):
            # Each triangle reuses the two previous vertices
            if i == 1:
                # The 4th vertex in a triangle strip is identical to the 2nd. This yields an invalid triangle, so should be skipped.
                continue
            if i % 2 == 0:
                triangles.append(
                    (
                        primitive.vertices[i],
                        primitive.vertices[i + 1],
                        primitive.vertices[i + 2],
                    )
                )
            else:
                # For every other triangle the winding order is flipped. Otherwise its face will be flipped.
                triangles.append(
                    (
                        primitive.vertices[i + 1],
                        primitive.vertices[i],
                        primitive.vertices[i + 2],
                    )
                )
        return triangles

    def serialize_positions(
        self, mesh_data: HSFMeshNodeData, obj_index: int
    ) -> ET.Element:
        """Serializes the vertex positions of all vertices in a mesh"""
        uid = f"{mesh_data.name}__{obj_index}"
        source = self.serialize_vertex_data_array(
            mesh_data.positions, f"{uid}-position"
        )
        technique = ET.SubElement(source, "technique_common")
        accessor = ET.SubElement(
            technique,
            "accessor",
            source=f"#{uid}-position-array",
            count=str(len(mesh_data.positions)),
            stride="3",
        )
        ET.SubElement(accessor, "param", name="X", type="float")
        ET.SubElement(accessor, "param", name="Y", type="float")
        ET.SubElement(accessor, "param", name="Z", type="float")
        return source

    def serialize_normals(
        self, mesh_data: HSFMeshNodeData, obj_index: int
    ) -> ET.Element:
        """Serializes the vertex normals of all vertices in a mesh"""
        uid = f"{mesh_data.name}__{obj_index}"
        source = self.serialize_vertex_data_array(mesh_data.normals, f"{uid}-normals")
        technique = ET.SubElement(source, "technique_common")
        accessor = ET.SubElement(
            technique,
            "accessor",
            source=f"#{uid}-normals-array",
            count=str(len(mesh_data.normals)),
            stride="3",
        )
        ET.SubElement(accessor, "param", name="X", type="float")
        ET.SubElement(accessor, "param", name="Y", type="float")
        ET.SubElement(accessor, "param", name="Z", type="float")
        return source

    def serialize_uvs(self, mesh_data: HSFMeshNodeData, obj_index: int) -> ET.Element:
        """Serializes the texture coordinates (uvs) of all vertices in a mesh"""
        uid = f"{mesh_data.name}__{obj_index}"
        source = self.serialize_vertex_data_array(
            # COLLADA assumes (1.0, 0.0) is the top-left corner; HSF assumes that's bottom-left
            list(map(lambda st: (st[0], 1 - st[1]), mesh_data.uvs)),
            f"{uid}-texcoord",
        )
        technique = ET.SubElement(source, "technique_common")
        accessor = ET.SubElement(
            technique,
            "accessor",
            source=f"#{uid}-texcoord-array",
            count=str(len(mesh_data.uvs)),
            stride="2",
        )
        ET.SubElement(accessor, "param", name="S", type="float")
        ET.SubElement(accessor, "param", name="T", type="float")
        return source

    def serialize_colors(
        self, mesh_data: HSFMeshNodeData, obj_index: int
    ) -> ET.Element:
        """Serializes the vertex colors of all vertices in a mesh"""
        uid = f"{mesh_data.name}__{obj_index}"
        source = self.serialize_vertex_data_array(mesh_data.colors, f"{uid}-colors")
        technique = ET.SubElement(source, "technique_common")
        accessor = ET.SubElement(
            technique,
            "accessor",
            source=f"#{uid}-colors-array",
            count=str(len(mesh_data.colors)),
            stride="4",
        )
        ET.SubElement(accessor, "param", name="R", type="float")
        ET.SubElement(accessor, "param", name="G", type="float")
        ET.SubElement(accessor, "param", name="B", type="float")
        ET.SubElement(accessor, "param", name="A", type="float")
        return source

    def serialize_vertex_data_array(
        self, data: list[tuple[int | float, ...]], name: str
    ):
        """Serializes a list of vertex data (e.g. coordinates or colors), flattening it and rounding it to 6 decimal places"""
        num_elements = 0 if len(data) == 0 else len(data[0])
        source = ET.Element("source", id=name)
        data_elem = ET.SubElement(
            source,
            "float_array",
            id=f"{name}-array",
            count=str(num_elements * len(data)),
        )

        data_elem.text = "\n".join(
            [" ".join([f"{coord:.6f}" for coord in coords]) for coords in data]
        )

        return source

    def _serialize_transformation_matrix(self, mtx: TransformationMatrix) -> str:
        """Serializes the node's local transforms (rotation, scale, position in XYZ) to a transformation Matrix"""
        return " ".join([f"{i:f}".rstrip("0").rstrip(".") for i in mtx.as_raw()])

    def serialize_visual_scene_replica(self, node: HSFNode) -> list[ET.Element]:
        """
        Serializes a REPLICA-node by copying over all descendants of the replicated node.
        """
        assert node.type == HSFNodeType.REPLICA
        res = []
        for child, _ in node.replica_data.replica.dfs():
            match child.type:
                case HSFNodeType.NULL1:
                    continue
                case HSFNodeType.MESH:
                    pass
                case _:
                    self._logger.warning(
                        f"Replica node {node.index} ({node.name}) attempts to copy over non-MESH child {child.index} ({child.name}; {child.type.name}) of replicated node {node.index} ({node.replica_data.replica.name})"
                    )
                    continue
            res.append(
                self.serialize_visual_scene_mesh(
                    child,
                    transform=(
                        node.hierarchy_data.world_transform()
                        * child.hierarchy_data.world_transform(
                            root_override=node.replica_data.replica
                        )
                    ),
                    name=f"{child.mesh_data.name}__{child.index}__{node.name}__{node.index}",
                )
            )
        return res

    def serialize_visual_scene_mesh(
        self,
        node: HSFNode,
        transform: TransformationMatrix = None,
        name: str = None,
    ) -> ET.Element:
        """
        Serialize an instance of a <geometry>. If `transform` is provided, uses that instead
        of the `node`'s transform.
        """
        assert node.type == HSFNodeType.MESH
        uid = f"{node.mesh_data.name}__{node.index}"
        if name is None:
            name = uid
        xml_node = ET.Element("node", id=name, name=name, type="NODE")
        # matrix = ET.SubElement(xml_node, "matrix", sid="transform")
        # A list of 16 floating-point values. These values are organized into a 4-by-4
        #   column-order matrix suitable for matrix composition.
        # trans_mtx = transform or node.hierarchy_data.world_transform()
        # matrix.text = self._serialize_transformation_matrix(trans_mtx)
        geo = ET.SubElement(
            xml_node, "instance_controller", url=f"#Armature_{uid}-skin"  # , name=name
        )

        ET.SubElement(geo, "skeleton").text = (
            f"#Armature_{self._data.root_node.name}__{self._data.root_node.index}"
        )
        bind_material = ET.SubElement(geo, "bind_material")
        technique = ET.SubElement(bind_material, "technique_common")

        attribute_indices = set()
        for primitive in node.mesh_data.primitives:
            if primitive.material_index == -1:
                continue
            attribute_indices.add(
                self._data.materials[primitive.material_index].attribute_index
            )
        for attribute_index in attribute_indices:
            if attribute_index == -1:
                continue
            instance_material = ET.SubElement(
                technique,
                "instance_material",
                symbol=f"material_{attribute_index:03}",
                target=f"#material_{attribute_index:03}",
            )
            # TODO: uv-coords
            # <bind_vertex_input semantic="UVMap" input_semantic="TEXCOORD" input_set="0"/>

        # <bind_material>
        #     <technique_common>
        #       <instance_material symbol="material_0" target="#material_0" />
        #     </technique_common>
        #   </bind_material>

        return xml_node

    def serialize_visual_scene_joint(self, node: HSFNode) -> ET.Element:
        """
        Serialize a node of type "JOINT".
        """
        assert node.type == HSFNodeType.NULL1
        uid = f"{node.name}__{node.index}"
        name = node.name
        xml_node = ET.Element(
            "node", id=f"Armature_{uid}", name=name, sid=uid, type="JOINT"
        )
        matrix = ET.SubElement(xml_node, "matrix", sid="transform")
        # A list of 16 floating-point values. These values are organized into a 4-by-4
        #   column-order matrix suitable for matrix composition.
        trans_mtx = node.hierarchy_data.local_transform()
        matrix.text = self._serialize_transformation_matrix(trans_mtx)
        return xml_node
