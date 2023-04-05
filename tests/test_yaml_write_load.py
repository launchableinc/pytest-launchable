import io
from yaml2obj.loader import YamlLoaderWithLineNumber
from yaml2obj.writer import YamlWriter

# 　Write YAML and read it with line numbers


def test_yaml_read_write():
    b = make_sample_yaml()
    v = YamlLoaderWithLineNumber.from_string(b)
    line_info = v["__line__"]
    assert v["key0"] == "value0"
    assert line_info["key0"] == 1
    assert line_info["key1"] == 2


# expected yaml
# key0: value0
# key1:
#  key11: value11

def make_sample_yaml() -> str:
    s = io.StringIO()
    writer = YamlWriter(s)
    writer.name("key0").value("value0")
    writer.name("key1").begin_object()
    writer.name("key11").value("value11")
    writer.end_object()
    return s.getvalue()
