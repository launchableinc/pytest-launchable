import pytest
from pytest_launchable.conftest import init_launchable_test_context, parse_pytest_item


def f():
    """empty method on this file"""
    return None


class T:
    """empty method on class T"""

    def m(self):
        return None


class PseudoPytest:
    """make pseudo pytest item"""

    def __init__(self, file: str, name: str, func_or_method, parameters: str = None):
        self.keywords = [file]
        self.originalname = name
        self._obj = func_or_method
        if parameters is not None:
            self.callspec = PseudoPytest.Callspec(parameters)

    class Callspec:
        def __init__(self, parameters: str):
            self._idlist = [parameters]


def test_parse_pytest_item():
    """Provide only the necessary attributes."""
    assert (None, "f", None) == parse_pytest_item(
        PseudoPytest("test_a.py", "f", f))
    t = T()
    assert ("T", "m", None) == parse_pytest_item(
        PseudoPytest("test_b.py", "m", t.m))
    assert ("T", "m", "[2-3-4]") == parse_pytest_item(
        PseudoPytest("test_b.py", "m", t.m, "2-3-4"))


def test_launchable_context():
    t = T()
    pytest_list = [PseudoPytest("test_a.py", "f", f), PseudoPytest(
        "test_b.py", "m", t.m), PseudoPytest("test_b.py", "m", t.m, "2-3-4")]
    testpath_list = ["file=test_a.py#testcase=f",
                     "file=test_b.py#class=T#testcase=m", "file=test_b.py#class=T#testcase=m[2-3-4]"]
    lc = init_launchable_test_context(pytest_list)
    assert lc.to_testpath_list() == testpath_list
    for i in range(len(pytest_list)):
        assert lc.find_testcase_from_testpath(
            testpath_list[i]).pytest_item == pytest_list[i]
