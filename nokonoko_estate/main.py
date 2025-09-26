import argparse
import os

from nokonoko_estate.parsers.file_parser import HSFFileParser
from nokonoko_estate.serializers.dae.file_serializer import HSFFileDAESerializer

# FILENAME = "resources/w05_file24.hsf"  # KTT board
# FILENAME = "resources/w05_file0.hsf"  # KTT map
# FILENAME = "resources/w03/file17.hsf"  # Boo start
# FILENAME = "resources/w03/file23.hsf"
# FILENAME = "resources/w03/file30.hsf"
OUTPUT_FOLDER = "output"

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        "Nokonoko-Estate-Exporter",
        description="Convert Mario Party 8 .hsf files to .dae",
        epilog="See https://github.com/Scutlet/Nokonoko-Estate-Exporter",
    )
    argparser.add_argument("filepath", help="Input .hsf file")
    argparser.add_argument("-o", "--output", help="Output folder")
    args = argparser.parse_args()
    FILENAME = args.filepath
    OUTPUT_FOLDER = args.output or OUTPUT_FOLDER

    print(f"Parsing {FILENAME} ...")
    parser = HSFFileParser(FILENAME)
    data = parser.parse_from_file()

    basename = os.path.splitext(os.path.basename(FILENAME))[0]
    os.makedirs(os.path.join(OUTPUT_FOLDER, basename, "images"), exist_ok=True)

    # parse_logpath = os.path.join(OUTPUT_FOLDER, basename, "parser.log")
    # print(f"Exporting parse log to {parse_logpath} ...")
    # with open(parse_logpath, "wb") as fl:
    #     fl.write(bytes([x.value for x in parser.get_parselog()]))

    print(
        f"Exporting textures to {os.path.join(OUTPUT_FOLDER, basename, 'images')} ..."
    )
    for name, tex in data.textures:
        # tex.show()
        name = name.replace("/", "")
        name = name.replace("\\", "")
        output_fp = f"{os.path.join(OUTPUT_FOLDER, basename, 'images', name)}.png"
        tex.save(output_fp)
        # print(f"\tExported texture to {output_fp}")

    print(
        f"Exporting model to {os.path.join(OUTPUT_FOLDER, basename, basename)}.dae ..."
    )
    serializer = HSFFileDAESerializer(
        data,
        f"{os.path.join(OUTPUT_FOLDER, basename, basename)}.dae",
    )
    serializer.serialize()
