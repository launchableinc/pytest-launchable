from yaml2obj.writer import YamlWriter
from launchable_cli_args.error_counter import ErrorCounter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from launchable_cli_args.cli_args import Commands


class RecordTestsArgs:
    def __init__(self, parent):
        self.parent = parent

    def fill_and_validate(self, data: dict, error_counter: ErrorCounter):
        if data is None:
            error_counter.record("record-tests section is empty")
        else:
            self.result_dir = data.get("result_dir", None)

    def write_to(self, writer: YamlWriter):
        writer.comment("The test results are placed here in JUnit XML format")
        writer.name("result_dir").value(self.result_dir)

    def to_command(self) -> "Commands":
        return ("launchable", "record", "tests", "--build", self.parent.eval_build_id(), "pytest", self.result_dir)

    @classmethod
    def auto_configure(cls, parent, path: str) -> "RecordTestsArgs":
        a = RecordTestsArgs(parent)
        a.result_dir = "launchable-test-result"
        return a
