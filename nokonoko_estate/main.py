from nokonoko_estate.parsers.file_parser import HSFFileParser
from nokonoko_estate.serializers.dae.file_serializer import HSFFileDAESerializer

FILENAME = "w05_file24.hsf"

if __name__ == "__main__":
    parser = HSFFileParser(FILENAME)
    data = parser.parse_from_file()

    # for x in parser._mesh_objects["bmerge2"].primitives:
    #     print(len(x.vertices))

    serializer = HSFFileDAESerializer(data, "output/test.dae")
    serializer.serialize()
