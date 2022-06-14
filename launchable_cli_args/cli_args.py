import os
from pathlib import Path
import subprocess
from typing import Callable, Optional, Tuple, Union

from yaml2obj.loader import YamlLoaderWithLineNumber
from yaml2obj.writer import YamlWriter

from launchable_cli_args.error_counter import ErrorCounter
from launchable_cli_args.recordbuild import RecordBuildArgs
from launchable_cli_args.recordsession import RecordSessionArgs
from launchable_cli_args.recordtests import RecordTestsArgs
from launchable_cli_args.subset import SubsetArgs


class CLIArgs:
    def __init__(self):
        self.record_build = RecordBuildArgs(self)
        self.record_session = RecordSessionArgs(self)
        self.subset = SubsetArgs(self)
        self.record_tests = RecordTestsArgs(self)
        self.target_dir: str = None

    # fill content and print message if necessary
    # 'data' should have line number information
    def fill_and_validate(self, data: dict):
        self.error_counter = ErrorCounter()
        self.source_object = data
        self.launchable_token = os.getenv("LAUNCHABLE_TOKEN")
        if self.launchable_token is None:
            self.error_counter.record(
                "environment variable LAUNCHABLE_TOKEN is not defined. please set it to enable Launchable features.")
        self.build_id: Optional[str] = data.get("build-name", None)
        self.cached_build_id = None
        if self.build_id is None:
            self.error_counter.record("build_id is not specified")
        self.record_build.fill_and_validate(
            data.get("record-build", None), self.error_counter)
        self.record_session.fill_and_validate(
            data.get("record-session", None), self.error_counter)
        self.subset.fill_and_validate(
            data.get("subset", None), self.error_counter)
        self.record_tests.fill_and_validate(
            data.get("record-tests", None), self.error_counter)

        if self.error_counter.error_count > 0:
            self.error_counter.print_errors()

    def write_to(self, writer: YamlWriter):
        writer.comment("Launchable test session configuration file")
        writer.comment(
            "See https://docs.launchableinc.com/resources/cli-reference for detailed usage of these options")
        writer.comment(" ")

        writer.name("schema-version").value("1.0")
        writer.name("build-name").value(self.build_id)

        writer.name("record-build").begin_object()
        self.record_build.write_to(writer)
        writer.end_object()

        writer.name("record-session").begin_object()
        self.record_session.write_to(writer)
        writer.end_object()

        writer.name("subset").begin_object()
        self.subset.write_to(writer)
        writer.end_object()

        writer.name("record-tests").begin_object()
        self.record_tests.write_to(writer)
        writer.end_object()

    def write_as_yaml(self, path: str):
        p = Path(path).resolve()
        p.parents[0].mkdir(parents=True, exist_ok=True)
        with p.open('w') as s:
            self.write_to(YamlWriter(s))

    # read value from dictionary and verify the content.
    # if error is not found, return the value itself
    # else, print error message with line number information and return None
    def check_mandatory_field(self, data: dict, key: str, verifier: Callable, error_counter: ErrorCounter) -> Optional[str]:
        value = data.get(key)
        line_info = data["__line__"]
        if value is None:
            error_counter.record("object from line %d: key %s is not found" % (
                line_info["__begin__"], key))
            return None
        else:
            msg = verifier(value)
            if msg is not None:
                error_counter.record("line %d: @%s: %s" %
                                     (line_info[key], key, msg))
                return None
            else:
                return value

    # parse optional integer field
    def check_int_field(self, data: dict, key: str, default_value: int, error_counter: ErrorCounter):
        value = data.get(key)
        line_info = data["__line__"]
        if value is None:
            # return default value
            return default_value
        else:
            try:
                return int(value)
            except:
                error_counter.record("line %d attribute %s: %s is not an integer" % (
                    line_info[key], key, str(value)))
                return None

    # surrently supported:
    # * "commit_hash" -> use commit hash as build id
    # * "$ENV" -> use environment variable as build id
    # * other -> use the value of conf file itself
    def eval_build_id(self):
        if self.cached_build_id is None:
            if self.build_id == "commit_hash":
                self.cached_build_id = git_rev_parse(self.target_dir)
            elif self.build_id[0] == "$":
                self.cached_build_id = os.getenv(self.build_id[1:])
            else:
                self.cached_build_id = self.build_id
        return self.cached_build_id

    # target_dir is the test files location path, specified at test execution.
    # for example, the unit test command is 'pytest <test_path>', target_dir is <test_path>
    @classmethod
    def from_yaml(cls, path: str, target_dir=None) -> "CLIArgs":
        args = CLIArgs()
        args.fill_and_validate(YamlLoaderWithLineNumber.from_file(path))
        args.target_dir = target_dir
        return args

    @classmethod
    def auto_configure(cls, path: str) -> "CLIArgs":
        args = CLIArgs()
        args.build_id = "commit_hash"
        args.cached_build_id = None
        args.record_build = RecordBuildArgs.auto_configure(args, path)
        args.record_session = RecordSessionArgs.auto_configure(args, path)
        args.subset = SubsetArgs.auto_configure(args, path)
        args.record_tests = RecordTestsArgs.auto_configure(args, path)
        return args

# get build id from commit hash


def git_rev_parse(dir: str) -> str:
    h = subprocess.run(("git", "rev-parse", "--short", "HEAD"),
                       cwd=dir, stdout=subprocess.PIPE, text=True).stdout
    print("launchable build id is configured by commit hash: %s" % (h))
    return h.strip()


Commands = Tuple[Optional[Union[str, int]], ...]
