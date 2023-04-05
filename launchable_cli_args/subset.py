from functools import reduce
from typing import TYPE_CHECKING, Optional
from launchable_cli_args.error_counter import ErrorCounter
from yaml2obj.writer import YamlWriter

if TYPE_CHECKING:
    from launchable_cli_args.cli_args import CLIArgs, Commands


class SubsetArgs:
    REST_FILE_NAME = "launchable_rest_file.txt"

    def __init__(self, parent: "CLIArgs"):
        self.parent = parent

    def fill_and_validate(self, data: dict, error_counter: ErrorCounter):
        if data is None:
            error_counter.record("subset section is empty")
        else:
            self.mode: str = data.get("mode", "record-only")
            if not self.mode in ["subset", "subset-and-rest", "record-only"]:
                error_counter.record(
                    "'mode' must be subset, subset-and-rest, or record-only")
            self.target: Optional[str] = data.get("target", None)
            self.confidence: Optional[int] = data.get("confidence", None)
            self.time: Optional[int] = data.get("time", None)
            if reduce(lambda a, e: a if e is None else a+1, [self.target, self.confidence, self.time], 0) != 1:
                error_counter.record(
                    "one of target/confidence/time must be specified")

    def write_to(self, writer: YamlWriter):
        writer.comment("mode can be subset, subset-and-rest, or record-only")
        writer.name("mode").value(self.mode)

        writer.comment(
            "if mode is subset or subset-and-rest, you must specify one of target/confidence/time")
        writer.comment("examples:")
        writer.comment(
            "  target: 30%  # Create a variable time-based subset of the given percentage. (0%-100%)")
        writer.comment(
            "  confidence: 30%  # Create a confidence-based subset of the given percentage. (0%-100%)")
        writer.comment("  time: 30m  # Create a fixed time-based subset. Select the best set of tests that run within the given time bound. (e.g. 10m for 10 minutes, 2h30m for 2.5 hours, 1w3d for 7+3=10 days. )")
        if getattr(self, "target", None) is not None:
            writer.name("target").value(self.target)
        if getattr(self, "confidence", None) is not None:
            writer.name("confidence").value(self.confidence)
        if getattr(self, "time", None) is not None:
            writer.name("time").value(self.time)

    def to_command(self) -> "Commands":
        if self.mode == "record-only":
            return ()  # subset command is not applicable
        else:
            a: "Commands" = ("launchable", "subset", "--build",
                             self.parent.eval_build_id())
            if getattr(self, "target", None) is not None:
                a += ("--target", self.target)
            if getattr(self, "confidence", None) is not None:
                a += ("--confidence", self.confidence)
            if getattr(self, "time", None) is not None:
                a += ("--time", self.time)

            if self.mode == "subset-and-rest":
                a += ("--rest", SubsetArgs.REST_FILE_NAME)

            a += ("pytest", )
            return a

    @classmethod
    def auto_configure(cls, parent: 'CLIArgs', path: str) -> "SubsetArgs":
        a = SubsetArgs(parent)
        a.mode = "record-only"
        a.confidence = 99
        return a
