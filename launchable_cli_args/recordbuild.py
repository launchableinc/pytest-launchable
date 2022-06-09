import os
from typing import TYPE_CHECKING, Optional
from yaml2obj.writer import YamlWriter
from launchable_cli_args.error_counter import ErrorCounter

if TYPE_CHECKING:
    from launchable_cli_args.cli_args import CLIArgs, Commands


class RecordBuildArgs:
    def __init__(self, parent: "CLIArgs"):
        self.parent = parent

    def fill_and_validate(self, data: dict, error_counter: ErrorCounter):
        def verify_source(path: str) -> Optional[str]:
            if not os.path.isdir(os.path.join(path, ".git")):
                return "the directory '%s' must be a git repository" % path
            else:
                return None

        if data is None:
            error_counter.record("record-build section is empty")
        else:
            self.source: Optional[str] = self.parent.check_mandatory_field(
                data, "source", verify_source, error_counter)
            self.max_days = self.parent.check_int_field(
                data, "max_days", 30, error_counter)

    def write_to(self, writer: YamlWriter):
        writer.comment("Put your git repository location here")
        writer.name("source").value(self.source)
        writer.name("max_days").value(self.max_days)

    def to_command(self) -> "Commands":
        a: "Commands" = ("launchable", "record", "build", "--name",
                         self.parent.eval_build_id(), "--source", self.source)
        if self.max_days != 30:
            a += ("--max-days", str(self.max_days))
        return a

    @classmethod
    def auto_configure(cls, parent, path: str) -> "RecordBuildArgs":
        a = RecordBuildArgs(parent)
        a.source = "."
        a.max_days = 30
        return a
