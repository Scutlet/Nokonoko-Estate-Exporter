from enum import Enum
from io import BufferedReader


class ParserLogger:
    """A logger that keeps track of which sections have been parsed"""

    class ParseType(Enum):
        PARSE_NONE = 0
        PARSE_READ = 1
        PARSE_PEEK = 2

    def __init__(self, reader: BufferedReader, file_size: int):
        self._reader = reader
        self._sz = file_size
        self.parselog: list[ParserLogger.ParseType] = [
            self.ParseType.PARSE_NONE for _ in range(file_size)
        ]

    def seek(self, target, whence=0):
        return self._reader.seek(target, whence)

    def tell(self):
        return self._reader.tell()

    def read(self, size=-1):
        assert size != -1, "Cannot log reading entire file!"
        pos = self._reader.tell()
        self.parselog[pos : pos + size] = [self.ParseType.PARSE_READ] * size
        return self._reader.read(size)

    def peek(self, size=0):
        pos = self._reader.tell()
        self.parselog[pos : pos + size] = [self.ParseType.PARSE_PEEK] * size
        return self._reader.peek(size)
