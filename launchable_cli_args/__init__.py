import os
import subprocess
from .recordbuild import RecordBuildArgs
from .recordsession import RecordSessionArgs
from .subset import SubsetArgs
from .recordtests import RecordTestsArgs
from .error_counter import ErrorCounter


class CLIArgs:
    def __init__(self):
        self.record_build = RecordBuildArgs(self)
        self.record_session = RecordSessionArgs(self)
        self.subset = SubsetArgs(self)
        self.record_tests = RecordTestsArgs(self)

    # fill content and print message if necessary
    # 'data' should have line number information
    def fill_and_validate(self, data: dict):
        error_counter = ErrorCounter()
        self.source_object = data
        self.error_counter = error_counter
        self.launchable_token = os.getenv("LAUNCHABLE_TOKEN")
        if self.launchable_token is None:
            error_counter.record(
                "environment variable LAUNCHABLE_TOKEN is not defined. please set it to enable Launchable features.")
        self.build_id = data.get("build-id", None)
        self.cached_build_id = None
        if self.build_id is None:
            error_counter.record("build_id is not specified")
        self.record_build.fill_and_validate(
            data.get("record-build", None), error_counter)
        self.record_session.fill_and_validate(
            data.get("record-session", None), error_counter)
        self.subset.fill_and_validate(data.get("subset", None), error_counter)
        self.record_tests.fill_and_validate(
            data.get("record-tests", None), error_counter)

    # read value from dictionary and verify the content.
    # if error is not found, return the value itself
    # else, print error message with line number information and return None
    def check_mandatory_field(self, data: dict, key: str, verifier: callable, error_counter: ErrorCounter):
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


def git_rev_parse(dir):
    h = subprocess.run(("git", "rev-parse", "--short", "HEAD"),
                       cwd=dir, stdout=subprocess.PIPE, text=True).stdout
    print("launchable build id is configured by commit hash: %s" % (h))
    return h.strip()
