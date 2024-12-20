from collections import defaultdict
from datetime import datetime
import logging
import xml.etree.ElementTree as ET

from PIL import Image

from nokonoko_estate.formats.enums import WrapMode
from nokonoko_estate.formats.formats import (
    HSFFile,
    AttributeObject,
    HSFNode,
    HSFNodeType,
    MeshObject,
    PrimitiveObject,
)
from nokonoko_estate.formats.matrix import RotationMatrix, TransformationMatrix

logger = logging.Logger(__name__)


EXPORT_ALL = True
MESH_WHITELIST = ["obj242", "oudan_all", "yazirusi_all", "obj127"]
MESH_WHITELIST = ["startdai", "oudan_all"]


class HSFFileDAESerializer:
    """Serializes HSF-data into a DAE-file"""

    def __init__(self, data: HSFFile, output_filepath: str):
        self._data = data
        self.output_path = output_filepath

    def serialize(self):
        """TODO"""
        root = ET.Element("COLLADA")
        root.set("xmlns", "http://www.collada.org/2005/11/COLLADASchema")
        root.set("version", "1.4.1")
        asset = ET.SubElement(root, "asset")
        contributor = ET.SubElement(asset, "contributor")
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
        library_materials = ET.SubElement(root, "library_materials")
        library_effects = ET.SubElement(root, "library_effects")
        for i, mat in enumerate(self._data.attributes):
            library_materials.append(self.serialize_material(mat, i))
            library_effects.append(self.serialize_effects(mat, i))

        # Geometry
        geometries = ET.SubElement(root, "library_geometries")
        for i, node in enumerate(
            filter(
                lambda node: node.node_data.type == HSFNodeType.MESH, self._data.nodes
            )
        ):
            if EXPORT_ALL or (
                "w05_file0.dae" not in self.output_path
                or node.mesh_data.name in MESH_WHITELIST
            ):
                geometries.append(self.serialize_geometry(node, i))
                node.node_data.attribute_index

        # Controller
        asset = ET.SubElement(root, "library_controllers")

        # Visual scenes
        visual_scenes = ET.SubElement(root, "library_visual_scenes")
        visual_scene = ET.SubElement(
            visual_scenes, "visual_scene", id="Scene", name="Scene"
        )
        for i, node in enumerate(
            filter(
                lambda node: node.node_data.type == HSFNodeType.MESH, self._data.nodes
            )
        ):
            # Add all meshes to the scene
            if EXPORT_ALL or (
                "w05_file0.dae" not in self.output_path
                or node.mesh_data.name in MESH_WHITELIST
            ):
                visual_scene.append(self.serialize_visual_scene(node, i))

        # Scene
        scene = ET.SubElement(root, "scene")
        instance_visual_scene = ET.SubElement(
            scene, "instance_visual_scene", url="#Scene"
        )

        ET.indent(root, space=" ", level=0)
        tree = ET.ElementTree(root)
        tree.write(self.output_path, encoding="utf-8", xml_declaration=True)
        # b_xml = ET.tostring(root)
        # print()
        # print(b_xml.decode("utf-8"))

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
        """TODO"""
        mat = ET.Element("material", id=f"material_{index:03}")
        ET.SubElement(mat, "instance_effect", url=f"#Effect_material_{index:03}")
        return mat

    def serialize_effects(self, material: AttributeObject, index: int) -> ET.Element:
        """TODO"""
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
        phong = ET.SubElement(technique, "phong")
        diffuse = ET.SubElement(phong, "diffuse")
        ET.SubElement(
            diffuse, "texture", texture=f"sampler_material_{index:03}", texcoord=""
        )
        if material.alpha_flag:
            transparent = ET.SubElement(phong, "transparent")
            ET.SubElement(
                transparent,
                "texture",
                texture=f"sampler_material_{index:03}",
                texcoord="",
            )

        return effect

    def serialize_geometry(self, node: HSFNode, obj_index: int) -> ET.Element:
        """TODO"""
        mesh_obj = node.mesh_data
        uid = f"{mesh_obj.name}__{obj_index}"

        geometry = ET.Element("geometry", id=f"{uid}-mesh", name=uid)
        mesh = ET.SubElement(geometry, "mesh")
        mesh.append(self.serialize_positions(mesh_obj, obj_index))
        # NORMALS
        mesh.append(self.serialize_uvs(mesh_obj, obj_index))
        # COLORS

        vertices = ET.SubElement(mesh, "vertices", id=f"{uid}-vertex")
        ET.SubElement(vertices, "input", semantic="POSITION", source=f"#{uid}-position")

        # Group primitives by material
        triangle_dict: dict[int, list[list[str]]] = defaultdict(list)
        polylist_dict: dict[int, list[list[str]]] = defaultdict(list)

        for primitive in mesh_obj.primitives:
            attribute_index = self._data.materials[
                primitive.material_index
            ].first_symbol

            match primitive.primitive_type:
                case PrimitiveObject.PrimitiveType.PRIMITIVE_TRIANGLE:
                    triangle_dict[attribute_index].append(
                        self.serialize_primitive_triangle(primitive)
                    )
                case PrimitiveObject.PrimitiveType.PRIMITIVE_QUAD:
                    polylist_dict[attribute_index].append(
                        self.serialize_primitive_quad(primitive)
                    )
                case _:
                    raise NotImplementedError(
                        f"Cannot serialize {primitive.primitive_type.name}"
                    )

        inputs = self._serialize_inputs(uid)
        for elem in self._serialize_primitive_dict(
            "polylist", polylist_dict, inputs, True
        ):
            mesh.append(elem)
        for elem in self._serialize_primitive_dict("triangles", triangle_dict, inputs):
            mesh.append(elem)
        return geometry

    def _serialize_primitive_dict(
        self,
        name: str,
        prim_dict: dict[int, list[list[str]]],
        extras: list[ET.Element],
        include_vcount=False,
    ) -> list[ET.Element]:
        """TODO"""
        xml_elems = []
        for attribute_index, serialized_primitives in prim_dict.items():
            polys = ET.Element(
                name,
                material=f"material_{attribute_index:03}",
                count=str(len(serialized_primitives)),
            )
            xml_elems.append(polys)

            for elem in extras:
                polys.append(elem)

            if include_vcount:
                input_sz = len(extras)
                vcount = ET.SubElement(polys, "vcount")
                vcount.text = " ".join(
                    [str(len(prim) // input_sz) for prim in serialized_primitives]
                )

            p_elem = ET.SubElement(polys, "p")
            p_elem.text = " ".join([" ".join(prim) for prim in serialized_primitives])
        return xml_elems

    def _serialize_inputs(self, mesh_obj_uid: str) -> list[ET.Element]:
        """TODO"""
        return [
            ET.Element(
                "input",
                semantic="VERTEX",
                source=f"#{mesh_obj_uid}-vertex",
                offset="0",
            ),
            # TODO: NORMAL
            ET.Element(
                "input",
                semantic="TEXCOORD",
                source=f"#{mesh_obj_uid}-texcoord",
                offset="1",  # 2
            ),
            # TODO: COLOR
        ]

    def serialize_primitive_triangle(self, primitive: PrimitiveObject) -> list[str]:
        """TODO"""
        assert (
            primitive.primitive_type == PrimitiveObject.PrimitiveType.PRIMITIVE_TRIANGLE
        )

        # The fourth primitive is a dummy and always references the first element in each array (position, normal, color, uv)
        # TODO: Fix attempted uv reading if there are no uv-coordinates
        return [
            str(primitive.vertices[0].position_index),
            str(primitive.vertices[0].uv_index),
            str(primitive.vertices[1].position_index),
            str(primitive.vertices[1].uv_index),
            str(primitive.vertices[2].position_index),
            str(primitive.vertices[2].uv_index),
        ]

    def serialize_primitive_quad(self, primitive: PrimitiveObject) -> list[str]:
        """TODO"""
        assert primitive.primitive_type == PrimitiveObject.PrimitiveType.PRIMITIVE_QUAD
        # The winding order of vertices produced is counter-clockwise and describes the front side of each polygon
        # Order in HSF-file: 0 1 3 2
        return [
            str(primitive.vertices[0].position_index),
            str(primitive.vertices[0].uv_index),
            str(primitive.vertices[1].position_index),
            str(primitive.vertices[1].uv_index),
            str(primitive.vertices[3].position_index),
            str(primitive.vertices[3].uv_index),
            str(primitive.vertices[2].position_index),
            str(primitive.vertices[2].uv_index),
        ]

    def serialize_positions(self, mesh_obj: MeshObject, obj_index: int) -> ET.Element:
        """TODO"""
        uid = f"{mesh_obj.name}__{obj_index}"
        source = self.serialize_vertex_data_array(mesh_obj.positions, f"{uid}-position")
        technique = ET.SubElement(source, "technique_common")
        accessor = ET.SubElement(
            technique,
            "accessor",
            source=f"#{uid}-position-array",
            count=str(len(mesh_obj.positions)),
            stride="3",
        )
        ET.SubElement(accessor, "param", name="X", type="float")
        ET.SubElement(accessor, "param", name="Y", type="float")
        ET.SubElement(accessor, "param", name="Z", type="float")
        return source

    def serialize_uvs(self, mesh_obj: MeshObject, obj_index: int) -> ET.Element:
        """TODO"""
        uid = f"{mesh_obj.name}__{obj_index}"
        source = self.serialize_vertex_data_array(
            # COLLADA assumes (1.0, 0.0) is the top-left corner; HSF assumes that's bottom-left
            list(map(lambda st: (st[0], 1 - st[1]), mesh_obj.uvs)),
            f"{uid}-texcoord",
        )
        technique = ET.SubElement(source, "technique_common")
        accessor = ET.SubElement(
            technique,
            "accessor",
            source=f"#{uid}-texcoord-array",
            count=str(len(mesh_obj.uvs)),
            stride="2",
        )
        ET.SubElement(accessor, "param", name="S", type="float")
        ET.SubElement(accessor, "param", name="T", type="float")
        return source

    def serialize_vertex_data_array(
        self, data: list[tuple[int | float, ...]], name: str
    ):
        """TODO"""
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

    def _serialize_transformation_matrix(self, node: HSFNode) -> str:
        """TODO"""
        transform = node.node_data.base_transform

        rot_mat = RotationMatrix.from_euler(transform.rotation, transform.scale)
        trans_mat = TransformationMatrix(rot_mat, transform.position).round()
        return " ".join([str(i) for i in trans_mat.as_raw()])

    def serialize_visual_scene(self, node: HSFNode, obj_index: int) -> ET.Element:
        """TODO"""
        mesh_obj = node.mesh_data
        uid = f"{mesh_obj.name}__{obj_index}"

        xml_node = ET.Element("node", id=uid, name=uid, type="NODE")
        matrix = ET.SubElement(xml_node, "matrix", sid="transform")
        # A list of 16 floating-point values. These values are organized into a 4-by-4
        #   column-order matrix suitable for matrix composition.
        matrix.text = self._serialize_transformation_matrix(node)
        geo = ET.SubElement(xml_node, "instance_geometry", url=f"#{uid}-mesh", name=uid)
        bind_material = ET.SubElement(geo, "bind_material")
        technique = ET.SubElement(bind_material, "technique_common")

        if node.node_data.name == "obj69":
            print(node.node_data.base_transform)
            print(node.node_data.current_transform)

        attribute_indices = set()
        for primitive in mesh_obj.primitives:
            attribute_indices.add(
                self._data.materials[primitive.material_index].first_symbol
            )
        for attribute_index in attribute_indices:
            instance_material = ET.SubElement(
                technique,
                "instance_material",
                symbol=f"material_{attribute_index:03}",
                target=f"#material_{attribute_index:03}",
            )
            # <bind_vertex_input semantic="UVMap" input_semantic="TEXCOORD" input_set="0"/>

        # <bind_material>
        #     <technique_common>
        #       <instance_material symbol="material_0" target="#material_0" />
        #     </technique_common>
        #   </bind_material>

        return xml_node

        # <node id="stair" name="stair" type="NODE">
        #     <matrix sid="transform">1 0 0 -233.378 0 1 0 -208.1444 0 0 1 786.8199 0 0 0 1</matrix>
        #     <instance_geometry url="#pPlane212__mtr_Road_Slope_001-mesh" name="stair">
        #     <bind_material>
        #         <technique_common>
        #         <instance_material symbol="mtr_Road_Slope-material" target="#mtr_Road_Slope-material">
        #             <bind_vertex_input semantic="pPlane212__mtr_Road_Slope-geometry-TEXCOORD" input_semantic="TEXCOORD" input_set="0"/>
        #             <bind_vertex_input semantic="pPlane212__mtr_Road_Slope-geometry-TEXCOORD1" input_semantic="TEXCOORD" input_set="1"/>
        #         </instance_material>
        #         </technique_common>
        #     </bind_material>
        #     </instance_geometry>
        # </node>
