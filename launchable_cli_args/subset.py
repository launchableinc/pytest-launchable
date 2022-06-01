from functools import reduce
from .error_counter import ErrorCounter


class SubsetArgs:
    REST_FILE_NAME = "launchable_rest_file.txt"

    def __init__(self, parent):
        self.parent = parent

    def fill_and_validate(self, data: dict, error_counter: ErrorCounter):
        if data is None:
            error_counter.record("subset section is empty")
        else:
            self.mode = data.get("mode", "subset")
            if not self.mode in ["subset", "subset_and_rest", "record_only"]:
                error_counter.record(
                    "'mode' must be subset, subset_and_rest, or record_only")
            self.target = data.get("target", None)
            self.confidence = data.get("confidence", None)
            self.time = data.get("time", None)
            if reduce(lambda a, e: a if e is None else a+1, [self.target, self.confidence, self.time], 0) != 1:
                error_counter.record(
                    "one of target/confidence/time must be specified")

    def to_command(self):
        if self.mode == "record_only":
            return ()  # subset command is not applicable
        else:
            a = ("launchable", "subset", "--build", self.parent.eval_build_id())
            if getattr(self, "target", None) is not None:
                a += ("--target", self.target)
            if getattr(self, "confidence", None) is not None:
                a += ("--confidence", self.confidence)
            if getattr(self, "time", None) is not None:
                a += ("--time", self.time)

            if self.mode == "subset_and_rest":
                a += ("--rest", SubsetArgs.REST_FILE_NAME)

            a += ("pytest", )
            return a

    @classmethod
    def auto_configure(cls, parent: 'CLIArgs', path: str) -> "SubsetArgs":
        a = SubsetArgs(parent)
        a.target = "30%"
        a.mode = "subset"
        return a
