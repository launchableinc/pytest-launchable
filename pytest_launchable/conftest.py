import subprocess
import re
import os
from typing import List, Optional, Tuple, Union

import pytest
from .memorizer import memorizer
from launchable_cli_args import CLIArgs
from lxml.builder import E  # type: ignore
from lxml import etree  # type: ignore

# global scope test session LaunchableTestContext
lc: Optional["LaunchableTestContext"] = None
cli: Optional[CLIArgs] = None

TestNameList = Tuple[Optional[str], str, Optional[str]]


class LaunchableTestContext:
    def __init__(self):
        self.enabled = True
        self.init()

    def init(self) -> None:
        self.test_node_list: List[LaunchableTestNode] = []

    def get_node_from_path(self, path: str) -> "LaunchableTestNode":
        for node in self.test_node_list:
            if node.path == path:
                return node
        node = LaunchableTestNode(path)
        self.test_node_list.append(node)
        return node

    def find_testcase_from_testpath(self, testpath: str) -> "LaunchableTestCase":
        @memorizer
        def testpath_re():
            return re.compile("file=(?P<file>([^#]+))(#class=(?P<class>([^#]+)))?#testcase=(?P<testcase>(.+))$")
        m = testpath_re().match(testpath)
        e = m.groupdict()

        # class is optional
        return self.get_node_from_path(e["file"]).find_test_case(e.get("class"), e["testcase"])

    def set_subset_command_request(self, command, input_files: List[str]) -> None:
        self.subset_command = command
        self.subset_input = input_files

    def set_subset_command_response(self, raw_subset: str, rest_file: Optional[str] = None) -> None:
        self.raw_subset = raw_subset
        self.raw_rest = read_test_path_list_file(
            rest_file) if rest_file is not None else None
        self.subset_list = format_test_path_list(self.raw_subset)
        self.rest_list = format_test_path_list(
            self.raw_rest) if rest_file is not None and self.raw_rest is not None else None

    def to_file_list(self) -> List[str]:
        return list(map(lambda n: n.path, self.test_node_list))

    def to_testpath_list(self) -> List[str]:
        r: List[str] = []
        for node in self.test_node_list:
            node.collect_testpath_list(r)
        return r

    def to_name_tuple_list(self) -> List[str]:
        r: List[str] = []
        for node in self.test_node_list:
            node.collect_name_tuple_list(r)
        return r

    # <class 'lxml.etree._Element'>  is this annotation "Element" correct?
    def junit_xml(self) -> etree._Element:
        array: List = []
        for node in self.test_node_list:
            node.collect_junit_element(array)
        launchable_extra = {'launchable_subset_command': " ".join(self.subset_command),  # command is tuple
                            'launchable_subset_input': ",".join(self.subset_input),
                            'launchable_raw_subset_response': self.raw_subset.replace("\r\n", ",")}
        if self.raw_rest is not None:
            launchable_extra['launchable_raw_rest_response'] = ",".join(
                self.raw_rest)
        return E.testsuites(E.testsuite(*array, name="pytest", **launchable_extra))

# for execution unit ( file )


class LaunchableTestNode:
    def __init__(self, path: str):
        self.path = path
        # array of the contents passed in pytest_collection_modifyitems()
        self.case_list: List[LaunchableTestCase] = []

    def add_test_case(self, pytest_item: pytest.Function, test_name_tuple: TestNameList):
        self.case_list.append(LaunchableTestCase(
            self, pytest_item, test_name_tuple))

    def short_str(self):
        return ",".join(map(lambda c: c.short_str(), self.case_list))

    def find_test_case(self, class_name: str, function_name_and_parameters: str):
        for testcase in self.case_list:
            if testcase.class_name == class_name and testcase.function_name_and_parameters == function_name_and_parameters:
                return testcase
        return None

    def collect_testpath_list(self, array: List[str]):
        for testcase in self.case_list:
            testcase.collect_testpath_list(array)

    def collect_name_tuple_list(self, array: List[str]):
        for testcase in self.case_list:
            array.append(str(testcase.test_name_tuple))

    def collect_pytest_items(self, category_name: str, items: List[pytest.Function]):
        for testcase in self.case_list:
            testcase.launchable_subset_category = category_name
            items.append(testcase.pytest_item)

    def collect_junit_element(self, array):
        for testcase in self.case_list:
            testcase.collect_junit_element(array)


class LaunchableTestCase:
    def __init__(self, parent_node: "LaunchableTestNode", pytest_item: pytest.Function, test_name_tuple: TestNameList):
        self.parent_node = parent_node
        self.pytest_item = pytest_item  # in unit test, this may be None
        self.test_name_tuple = test_name_tuple
        self.class_name: Optional[str] = test_name_tuple[0]  # optional
        self.function_name = test_name_tuple[1]  # mandatory
        self.parameters: Optional[str] = test_name_tuple[2]  # optional
        self.function_name_and_parameters = self.function_name
        if self.parameters is not None:
            # then 'function_name[0-1]' style
            self.function_name_and_parameters += self.parameters
        # this is set after calling subset service
        self.launchable_subset_category = "unknown"

    def collect_testpath_list(self, array: List[str]):
        if self.class_name is None:
            array.append("file=%s#testcase=%s" % (
                self.parent_node.path, self.function_name_and_parameters))
        else:
            array.append("file=%s#class=%s#testcase=%s" % (
                self.parent_node.path, self.class_name, self.function_name_and_parameters))

    def short_str(self) -> str:
        return "file=%s class=%s testcase=%s params=%s" % (self.parent_node.path, self.class_name, self.function_name, self.parameters)

    def set_result(self, pytest_result):
        if pytest_result.when == "setup":
            self.setup_result = pytest_result
        elif pytest_result.when == "teardown":
            self.teardown_result = pytest_result
        elif pytest_result.when == "call":
            self.call_result = pytest_result
        else:
            raise("unexpected 'when' %s" % pytest_result.when)

    def collect_junit_element(self, array: List) -> None:
        if not hasattr(self, "call_result"):
            return
        output_classname = self.parent_node.path.replace(".py", "").replace(
            "/", ".")  # ugly, but actual junit result is this pattern
        output_function_name = self.function_name
        if self.parameters is not None:
            # then output_function_name is 'some_functin[0-1]' style
            output_function_name += self.parameters

        if self.class_name is None:
            launchable_test_path = "file=%s#testcase=%s" % (
                self.parent_node.path, output_function_name)
        else:
            output_classname += "." + self.class_name
            launchable_test_path = "file=%s#class=%s#testcase=%s" % (
                self.parent_node.path, self.class_name, output_function_name)

        content: Union[etree._Element, str] = ""
        message: str = ""
        if self.call_result.outcome == 'failed':
            message = ""
            # copied from junit formatter of pytest
            if hasattr(self.call_result.longrepr, "reprcrash"):
                message = self.call_result.longrepr.reprcrash.message
            content = E.failure(
                str(self.call_result.longrepr), message=message)
        array.append(E.testcase(content,
                                classname=output_classname,
                                name=output_function_name,
                                time=str(self.call_result.duration),
                                setup_time=str(self.setup_result.duration),
                                teardown_time=str(
                                    self.teardown_result.duration),
                                launchable_test_path=launchable_test_path,
                                launchable_subset_category=self.launchable_subset_category))


def is_pytest_test_file(path: str) -> bool:
    """check the path is pytest test file or not"""
    @memorizer
    def pytest_test_file_re():
        return re.compile(".*test_.*\.py$")
    return pytest_test_file_re().match(path)


def read_test_path_list_file(filename: str) -> List[str]:
    with open(filename) as file:
        lines = file.readlines()
        return [line.rstrip() for line in lines]


def format_test_path_line(line: str) -> str:
    """modify curious Launchable CLI output"""
    d = line.index("::")
    return line if d == -1 else line[0:d]


def format_test_path_list(input: Union[List, str]) -> List[str]:
    # avoid "file::file" case. it seems to be a bug of subset command
    if not isinstance(input, list):  # both of list/string are capable
        input = input.split("\n")
    r = []
    for e in input:
        e = e.strip()
        if len(e) > 0:
            r.append(format_test_path_line(e))
    return r


def pytest_addoption(parser):
    # sample for introducing custom command line option
    group = parser.getgroup("launchable arguments")
    group.addoption('--launchable', '--launchable',
                    action="store_true",
                    dest="launchable",
                    help="enable launchable feature")
    group.addoption('--launchable-conf-path', '--launchable-conf-path',
                    action="store",
                    dest="launchable_conf_path",
                    metavar="",
                    default="launchable.conf",
                    help="path of launchable test configuration file")


def pytest_configure(config) -> None:
    global cli, lc
    test_target = config.option.file_or_dir[0]
    lc = LaunchableTestContext()
    lc.enabled = True if (hasattr(config, "option")
                          and config.option.launchable) else False
    print("config="+str(config.__class__))

    if lc.enabled:
        conf_file_path = config.option.launchable_conf_path
        cli = CLIArgs.from_yaml(conf_file_path, target_dir=test_target)
        subprocess.run(("launchable", "verify"))
        subprocess.run(cli.record_build.to_command())
        subprocess.run(cli.record_session.to_command())


def init_launchable_test_context(items: List[pytest.Function]) -> "LaunchableTestContext":
    if lc is None:
        raise Exception("launchable test context is not initialized")

    lc.init()
    for testcase in items:
        lc_node: Optional[LaunchableTestNode] = None
        # keywords is defined in pytest class NodeKeywords
        for k in testcase.keywords:
            # we got parameters as fllowing key: pytestmark [Mark(name='parametrize', args=('x', [1.0, 0.0]), kwargs={})]
            if is_pytest_test_file(k):
                lc_node = lc.get_node_from_path(k)
        test_names = parse_pytest_item(testcase)
        if lc_node is not None:
            lc_node.add_test_case(testcase, test_names)
    return lc

# called for each test file... this hook can be used to collect full path of tests
# def pytest_collect_file(path):
#	print("collect_file path=%s testcasecount=%d" % (path, len(lc.test_node_list))) # 'path' is full path

# this hook receives test case list
# we get a chance of reordering or subsetting at this point


def pytest_collection_modifyitems(config, items: List[pytest.Function]) -> None:
    if lc is None:
        raise Exception("launchable test context is not initialized")

    if not lc.enabled:
        return

    init_launchable_test_context(items)

    if cli is None:
        raise Exception("cli args is not initialized")

    # call subset
    # file_list = lc.to_file_list()
    # hack for testcase omittion
    # CLI cannot handle filename-only test cases
    # file_list = list(map(lambda x: (x + "::" + x), file_list))

    subset_command = cli.subset.to_command()

    # No intervention in the original testcase collection ( "record-only" mode )
    if len(subset_command) == 0:
        return

    testpath_list = lc.to_testpath_list()
    lc.set_subset_command_request(subset_command, testpath_list)
    raw_subset_result = subprocess.run(subset_command, input="\r\n".join(
        testpath_list), stdout=subprocess.PIPE, text=True)
    if cli.subset.mode == "subset_and_rest":
        lc.set_subset_command_response(
            raw_subset_result.stdout, cli.subset.REST_FILE_NAME)
    else:
        lc.set_subset_command_response(raw_subset_result.stdout)
    #print("input_file_list=" + str(file_list))
    #print("output_file_list=" + str(lc.subset_list))
    #print("all collected names " + str(lc.to_name_tuple_list()))

    # find testcase , mark category name, and return pytest object
    def find_and_mark(testpath: str, category: str):
        if lc is None:
            raise Exception("launchable test context is not initialized")

        testcase = lc.find_testcase_from_testpath(testpath)
        if testcase is None:
            raise Exception("testpath %s not found" % testpath)
        testcase.launchable_subset_category = category
        return testcase.pytest_item

    items.clear()
    for name in lc.subset_list:
        items.append(find_and_mark(name, "subset"))
    if lc.rest_list is not None:
        for name in lc.rest_list:
            items.append(find_and_mark(name, "rest"))

# called for each test case
# at this stage, 'location' attribute is added to `item`
# def pytest_runtest_setup(item):

# receiving the test result
# this is called 3 times (setup/call/teardown) for each test case.


def pytest_runtest_logreport(report):
    if not lc.enabled:
        return
    # sample of nodeid: 'calc_example/math/test_mul.py::TestMul::test_mul_int1'
    ids = report.nodeid.split("::")
    node = lc.get_node_from_path(ids[0])
    # class_name can be empty
    class_name = ids[1] if len(ids) == 3 else None
    # parametrize part is in this func_name field
    func_name = ids[2] if len(ids) == 3 else ids[1]
    test_case = node.find_test_case(class_name, func_name)
    if test_case == None:
        print("result node not found class=%s func=%s" %
              (class_name, func_name))
    else:
        test_case.set_result(report)

# cleanup session


def pytest_sessionfinish(session):
    if lc is None:
        raise Exception("launchable test context is not initialized")

    if not lc.enabled:
        return
    if not os.path.exists(cli.record_tests.result_dir):
        os.makedirs(cli.record_tests.result_dir)
    report = lc.junit_xml()
    test_result_file = os.path.join(
        cli.record_tests.result_dir, "test-results.xml")
    out_strm = open(test_result_file, "w", encoding="utf-8")
    out_strm.write(etree.tostring(
        report, encoding="unicode", pretty_print=True))
    out_strm.close()
    record_test_command = cli.record_tests.to_command()
    subprocess.run(record_test_command)


def parse_pytest_item(testcase: pytest.Function) -> TestNameList:
    class_name: Optional[str] = None
    parameters: Optional[str] = None
    function_name = testcase.originalname
    # _obj is function(belonging to a file) or method(belonging to a class). this is determined by checking it has __self__
    if hasattr(testcase._obj, "__self__"):
        class_name = testcase._obj.__self__.__class__.__name__
    if hasattr(testcase, "callspec"):  # only parametrized tests have 'callspec'
        # test name in result object has paramters as [x-y-z] style
        parameters = "["+testcase.callspec._idlist[0]+"]"
    n = (class_name, function_name, parameters)
    return n
    # example of parametrized test
    # {'keywords': <NodeKeywords for node <Function test_params[1-5-6]>>,
    # 'own_markers': [Mark(name='parametrize', args=('a,b,c', [(1, 2, 3), (1, 5, 6)]), kwargs={})],
    # 'extra_keyword_matches': set(), 'stash': <_pytest.stash.Stash object at 0x7f68f876fac0>,
    # '_report_sections': [], 'user_properties': [], 'originalname': 'test_params', '_obj': <function test_params at 0x7f68f8772310>,
    # 'callspec': CallSpec2(funcargs={}, params={'a': 1, 'b': 5, 'c': 6}, indices={'a': 1, 'b': 1, 'c': 1},
    # _arg2scope={'a': <Scope.Function: 'function'>, 'b': <Scope.Function: 'function'>, 'c': <Scope.Function: 'function'>},
    # _idlist=['1-5-6'], marks=[]), '_fixtureinfo': FuncFixtureInfo(argnames=('a', 'b', 'c'),
    #  initialnames=('a', 'b', 'c'), names_closure=['a', 'b', 'c'],
    # name2fixturedefs={'a': [<FixtureDef argname='a' scope='function' baseid=''>],
    # 'b': [<FixtureDef argname='b' scope='function' baseid=''>],
    # 'c': [<FixtureDef argname='c' scope='function' baseid=''>]}),
    #  'fixturenames': ['a', 'b', 'c'], 'funcargs': {}, '_request': <FixtureRequest for <Function test_params[1-5-6]>>}
