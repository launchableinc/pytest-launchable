from .error_counter import ErrorCounter

class RecordTestsArgs:
    def __init__(self, parent):
        self.parent = parent
    def fill_and_validate(self, data:dict, error_counter:ErrorCounter):
        if data is None:
            error_counter.record("record-tests section is empty")
        else:
            self.result_dir = data.get("result_dir", None)

    def to_command(self):
        return ("launchable", "record", "tests", "--build", self.parent.eval_build_id(), "pytest", self.result_dir)

    @classmethod
    def auto_configure(cls, parent, path:str) -> "RecordTestsArgs":
        a = RecordTestsArgs(parent)
        a.result_dir = "launchable-test-result"
        return a
