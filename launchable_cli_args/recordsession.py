from yaml2obj.writer import YamlWriter

from launchable_cli_args.error_counter import ErrorCounter


class RecordSessionArgs:
    def __init__(self, parent):
        self.parent = parent

    def fill_and_validate(self, data: dict, error_counter: ErrorCounter):
        # record-session section is can be empty
        return 0

    def write_to(self, writer: YamlWriter):
        return

    def to_command(self):
        return ("launchable", "record", "session", "--build", self.parent.eval_build_id())

    # returning an instance of this class(RecordSessionArgs) requires `from __future__ import annotations`
    @classmethod
    def auto_configure(cls, parent, path: str) -> "RecordSessionArgs":
        a = RecordSessionArgs(parent)
        return a
