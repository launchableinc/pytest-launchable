import io
import os
from typing import Any
import yaml
from yaml.loader import SafeLoader
from yaml.composer import Composer
from yaml.constructor import Constructor

#


class YamlLoaderWithLineNumber(SafeLoader):
    def __init__(self, stream):
        super(YamlLoaderWithLineNumber, self).__init__(stream)

    def compose_node(self, parent, index):
        node = Composer.compose_node(self, parent, index)
        node.__line__ = self.line + 1
        return node

    def construct_mapping(self, node, deep=False):
        line_info = {}
        min_line = 100000
        for k, _ in node.value:
            line_info[k.value] = k.__line__
            min_line = min(min_line, k.__line__)
        # the object starts from line number __begin__
        line_info["__begin__"] = min_line

        mapping = Constructor.construct_mapping(self, node, deep=deep)
        mapping["__line__"] = line_info
        return mapping

    @classmethod
    def from_file(cls, path: str) -> Any:
        with open(path) as file:
            o = yaml.load(file, Loader=YamlLoaderWithLineNumber)
            o['__fullpath__'] = os.path.abspath(path)
            return o

    @classmethod
    def from_string(cls, body: str) -> Any:
        return yaml.load(io.StringIO(body), Loader=YamlLoaderWithLineNumber)
