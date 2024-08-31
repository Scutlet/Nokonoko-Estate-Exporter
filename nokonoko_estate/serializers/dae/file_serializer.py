import logging
import xml.etree.ElementTree as ET

from nokonoko_estate.formats import HSFFile, MeshObject, PrimitiveObject


logger = logging.Logger(__name__)


class HSFFileDAESerializer:
    """Serializes HSF-data into a DAE-file"""

    def __init__(self, data: HSFFile, output_filepath: str):
        self._data = data
        self.output_path = output_filepath

    def serialize(self):
        """TODO"""
        header = '<?xml version="1.0" encoding="utf-8"?>'
        root = ET.Element("COLLADA")
        root.set("xmlns", "http://www.collada.org/2005/11/COLLADASchema")
        root.set("version", "1.4.1")
        asset: ET.Sub = ET.SubElement(root, "asset")
        author: ET.Sub = ET.SubElement(asset, "author")
        author.text = "NokonokoEstateExporter"
        up_axis: ET.Sub = ET.SubElement(asset, "up_axis")
        up_axis.text = "Y_UP"

        # Images
        asset = ET.SubElement(root, "library_images")

        # Materials
        asset = ET.SubElement(root, "library_materials")

        # Effects
        asset = ET.SubElement(root, "library_effects")

        # Geometry
        geometries = ET.SubElement(root, "library_geometries")
        for mesh_obj in self._data.mesh_objects.values():
            geometries.append(self.serialize_geometry(mesh_obj))

        # Controller
        asset = ET.SubElement(root, "library_controllers")

        # Visual scenes
        visual_scenes = ET.SubElement(root, "library_visual_scenes")
        visual_scene = ET.SubElement(
            visual_scenes, "visual_scene", id="Scene", name="Scene"
        )
        for mesh_obj in self._data.mesh_objects.values():
            # Add all meshes to the scene
            visual_scene.append(self.serialize_visual_scene(mesh_obj))

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

    def serialize_geometry(self, mesh_obj: MeshObject) -> ET.Element:
        """TODO"""

        geometry = ET.Element(
            "geometry", id=f"{mesh_obj.name}-mesh", name=mesh_obj.name
        )
        mesh = ET.SubElement(geometry, "mesh")
        mesh.append(self.serialize_positions(mesh_obj))
        # mesh.append(
        #     self.serialize_vertex_data_array(
        #         mesh_obj.normals, f"{mesh_obj.name}-normal"
        #     )
        # )
        # mesh.append(
        #     self.serialize_vertex_data_array(mesh_obj.uvs, f"{mesh_obj.name}-textcoord")
        # )
        # mesh.append(
        #     self.serialize_vertex_data_array(mesh_obj.colors, f"{mesh_obj.name}-color")
        # )

        vertices = ET.SubElement(mesh, "vertices", id=f"{mesh_obj.name}-vertex")
        ET.SubElement(
            vertices, "input", semantic="POSITION", source=f"#{mesh_obj.name}-position"
        )

        # These index the mesh vertices
        polygons = ET.SubElement(mesh, "polylist", count="1")  # material=foo
        triangles = ET.SubElement(mesh, "triangles", count="1")  # material=foo

        input_vertex_tri = ET.SubElement(
            triangles,
            "input",
            semantic="VERTEX",
            source=f"#{mesh_obj.name}-vertex",
            offset="0",
        )
        input_vertex_poly = ET.SubElement(
            polygons,
            "input",
            semantic="VERTEX",
            source=f"#{mesh_obj.name}-vertex",
            offset="0",
        )
        vcount_poly = ET.SubElement(polygons, "vcount")
        p_tri = ET.SubElement(triangles, "p")
        p_poly = ET.SubElement(polygons, "p")

        vcount_poly_elems: list[str] = []
        p_tri_elems: list[str] = []
        p_poly_elems: list[str] = []

        # p_tri.text = "0 1 2 3 4 5"

        for primitive in mesh_obj.primitives:
            match primitive.primitive_type:
                case PrimitiveObject.PrimitiveType.PRIMITIVE_TRIANGLE:
                    p_tri_elems += self.serialize_primitive_triangle(primitive)
                case PrimitiveObject.PrimitiveType.PRIMITIVE_QUAD:
                    vcount_poly_elems.append("4")
                    p_poly_elems += self.serialize_primitive_quad(primitive)
                case _:
                    raise NotImplementedError(
                        f"Cannot serialize {primitive.primitive_type.name}"
                    )

        vcount_poly.text = " ".join(vcount_poly_elems)
        p_tri.text = " ".join(p_tri_elems)
        p_poly.text = " ".join(p_poly_elems)

        triangles.attrib["count"] = str(len(p_tri_elems) // 3)
        polygons.attrib["count"] = str(len(vcount_poly_elems))

        # COLLADA uses a right-handed coordinate system; (0, 0) is the bottom-left of an image
        # textcoord = ET.SubElement(mesh, "mesh")
        # normal = ET.SubElement(mesh, "mesh")
        # color = ET.SubElement(mesh, "mesh")

        return geometry

    def serialize_primitive_triangle(self, primitive: PrimitiveObject) -> list[str]:
        """TODO"""
        assert (
            primitive.primitive_type == PrimitiveObject.PrimitiveType.PRIMITIVE_TRIANGLE
        )
        raise NotImplementedError("Cannot serialize triangles")

    def serialize_primitive_quad(self, primitive: PrimitiveObject) -> list[str]:
        """TODO"""
        assert primitive.primitive_type == PrimitiveObject.PrimitiveType.PRIMITIVE_QUAD
        # The winding order of vertices produced is counter-clockwise and describes the front side of each polygon
        # Order in HSF-file: 0 1 3 2
        return [
            str(primitive.vertices[0].position_index),
            str(primitive.vertices[1].position_index),
            str(primitive.vertices[3].position_index),
            str(primitive.vertices[2].position_index),
        ]

    def serialize_positions(self, mesh_obj: MeshObject) -> ET.Element:
        source = self.serialize_vertex_data_array(
            mesh_obj.positions, f"{mesh_obj.name}-position"
        )
        technique = ET.SubElement(source, "technique_common")
        accessor = ET.SubElement(
            technique,
            "accessor",
            source=f"#{mesh_obj.name}-position-array",
            count=str(len(mesh_obj.positions)),
            stride="3",
        )
        ET.SubElement(accessor, "param", name="X", type="float")
        ET.SubElement(accessor, "param", name="Y", type="float")
        ET.SubElement(accessor, "param", name="Z", type="float")
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

    def serialize_visual_scene(self, mesh_obj: MeshObject) -> ET.Element:
        """TODO"""
        node = ET.Element("node", id=mesh_obj.name, name=mesh_obj.name, type="NODE")
        matrix = ET.SubElement(node, "matrix", sid="transform")
        # ???
        matrix.text = "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"
        geo = ET.SubElement(
            node, "instance_geometry", url=f"#{mesh_obj.name}-mesh", name=mesh_obj.name
        )
        return node

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
