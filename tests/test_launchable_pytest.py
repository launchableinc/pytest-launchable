from typing import Optional, Callable
import pytest
from pytest_launchable.launchable_test_context import PytestTestPath, init_launchable_test_context, parse_pytest_item


def f():
    """empty method on this file"""
    return None


class T:
    """empty method on class T"""

    def m(self):
        return None


class PseudoPytest:
    """make pseudo pytest item"""

    def __init__(self, file: str, name: str, func_or_method: Callable, parameters: Optional[str] = None):
        class_name = func_or_method.__self__.__class__.__name__ if hasattr(  # type: ignore
            func_or_method, "__self__") else None
        function = name + f'[{parameters}]' if parameters else name
        self.keywords = [file]
        self.nodeid = "::".join(
            (file, class_name, function)) if class_name else "::".join((file, function))
        self._obj = func_or_method

    class Callspec:
        def __init__(self, parameters: str):
            self._idlist = [parameters]


def test_parse_pytest_item():
    """Provide only the necessary attributes."""
    assert PytestTestPath("test_a.py", None, "f", None) == parse_pytest_item(
        PseudoPytest("test_a.py", "f", f))
    t = T()
    assert PytestTestPath("test_b.py", "T", "m", None) == parse_pytest_item(
        PseudoPytest("test_b.py", "m", t.m))
    assert PytestTestPath("test_b.py", "T", "m", "[2-3-4]") == parse_pytest_item(
        PseudoPytest("test_b.py", "m", t.m, "2-3-4"))


def test_launchable_context():
    t = T()
    pytest_list = [PseudoPytest("test_a.py", "f", f), PseudoPytest(
        "test_b.py", "m", t.m), PseudoPytest("test_b.py", "m", t.m, "2-3-4")]
    testpath_list = ["test_a.py::f",
                     "test_b.py::T::m", "test_b.py::T::m[2-3-4]"]
    lc = init_launchable_test_context(pytest_list)
    assert lc.to_testpath_list() == testpath_list
    for i in range(len(pytest_list)):
        assert lc.find_testcase_from_testpath(
            testpath_list[i]).pytest_item == pytest_list[i]
