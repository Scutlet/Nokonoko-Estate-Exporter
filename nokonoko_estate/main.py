import os

from nokonoko_estate.parsers.file_parser import HSFFileParser
from nokonoko_estate.serializers.dae.file_serializer import HSFFileDAESerializer

FILENAME = "resources/w05_file24.hsf"
# FILENAME = "resources/w05_file0.hsf"
OUTPUT_FOLDER = "output"

if __name__ == "__main__":
    parser = HSFFileParser(FILENAME)
    data = parser.parse_from_file()

    basename = os.path.splitext(os.path.basename(FILENAME))[0]
    os.makedirs(os.path.join(OUTPUT_FOLDER, basename, "images"), exist_ok=True)

    for name, tex in data.textures:
        # tex.show()
        name = name.replace("/", "")
        name = name.replace("\\", "")
        output_fp = f"{os.path.join(OUTPUT_FOLDER, basename, 'images', name)}.png"
        tex.save(output_fp)
        # print(f"Exported texture to {output_fp}")

    serializer = HSFFileDAESerializer(
        data,
        f"{os.path.join(OUTPUT_FOLDER, basename, basename)}.dae",
    )
    serializer.serialize()
