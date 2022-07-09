import json

from .exporter import Exporter


class FileExporter(Exporter):
    def __init__(self, path) -> None:
        super().__init__()
        self.__path = path

    def export(self, results: list) -> None:
        with open(self.__path, "w") as f:
            f.write(json.dumps(results, indent=4, sort_keys=False))
