import argparse
import logging
import os

logger = logging.getLogger(__name__)

from nokonoko_estate.parsers.file_parser import HSFFileParser
from nokonoko_estate.serializers.dae.file_serializer import HSFFileDAESerializer

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        "Nokonoko-Estate-Exporter",
        description="Convert Mario Party 8 .hsf files to .dae",
        epilog="See https://github.com/Scutlet/Nokonoko-Estate-Exporter",
    )
    argparser.add_argument("filepath", help="Input .hsf file")
    argparser.add_argument("-o", "--output", help="Output folder")
    argparser.add_argument("-v", "--verbose", action="store_true")
    args = argparser.parse_args()
    FILENAME = args.filepath
    OUTPUT_FOLDER = args.output or "output"

    basename = os.path.splitext(os.path.basename(FILENAME))[0]
    os.makedirs(os.path.join(OUTPUT_FOLDER, basename, "images"), exist_ok=True)

    level = logging.DEBUG if args.verbose else logging.INFO
    # Logging
    logging.basicConfig(
        filename=os.path.join(OUTPUT_FOLDER, basename, "out.log"),
        level=level,
        filemode="w",
        format="%(asctime)s %(name)s [%(levelname)s] > %(message)s",
    )

    logger.info(f"Parsing {FILENAME} ...")
    parser = HSFFileParser(FILENAME)
    data = parser.parse_from_file()

    # parse_logpath = os.path.join(OUTPUT_FOLDER, basename, "parser.log")
    # logger.info(f"Exporting parse log to {parse_logpath} ...")
    # with open(parse_logpath, "wb") as fl:
    #     fl.write(bytes([x.value for x in parser.get_parselog()]))

    if data.textures:
        logger.info(
            f"Exporting textures to {os.path.join(OUTPUT_FOLDER, basename, 'images')} ..."
        )
        textures: list[str] = []
        for name, tex in data.textures:
            # tex.show()
            name = name.replace("/", "")
            name = name.replace("\\", "")
            output_fp = f"{os.path.join(OUTPUT_FOLDER, basename, 'images', name)}.png"
            tex.save(output_fp)
            logger.debug(f"\t - Exported texture to {output_fp}")
            textures.append(f"{name}.png")

        logger.info(f"Exported {len(textures)} texture(s) > {', '.join(textures)}")
        logger.info(
            f"Exporting model to {os.path.join(OUTPUT_FOLDER, basename, basename)}.dae ..."
        )
        serializer = HSFFileDAESerializer(
            data,
            f"{os.path.join(OUTPUT_FOLDER, basename, basename)}.dae",
        )
        serializer.serialize()
    logger.info(f"Export complete!")
