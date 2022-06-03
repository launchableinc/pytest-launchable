# write object tree to text stream as YAML format

from io import TextIOWrapper
from typing import List


class YamlWriter:
    def __init__(self, stream: TextIOWrapper):
        self.stream = stream
        self.level = 0
        self.array_levels: List[int] = []  # memorize array

    def name(self, key: str) -> "YamlWriter":
        self.__indent()
        self.stream.write(key)
        self.stream.write(":")
        return self

    def value(self, value) -> "YamlWriter":
        if self.level in self.array_levels:
            self.__indent()
            self.stream.write("- ")
        else:
            self.stream.write(" ")
        self.stream.write(str(value))
        self.stream.write("\n")
        return self

    def begin_object(self) -> "YamlWriter":
        if self.level in self.array_levels:
            self.__indent()
            self.stream.write("-")
        self.stream.write("\n")
        self.level = self.level + 1
        return self

    def end_object(self) -> "YamlWriter":
        if self.level <= 0:
            raise Exception("level is already 0")
        self.level = self.level - 1
        return self

    def begin_array(self) -> "YamlWriter":
        self.array_levels.insert(0, self.level)
        self.stream.write("\n")
        return self

    def end_array(self) -> "YamlWriter":
        self.array_levels.pop(0)
        return self

    def comment(self, body: str) -> "YamlWriter":
        self.__indent()
        self.stream.write("# ")
        self.stream.write(body)
        self.stream.write("\n")
        return self

    def __indent(self) -> "YamlWriter":
        for _ in range((self.level + len(self.array_levels)) * 2):
            self.stream.write(" ")
        return self
