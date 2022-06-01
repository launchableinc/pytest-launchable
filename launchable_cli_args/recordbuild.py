import os

from .error_counter import ErrorCounter

class RecordBuildArgs:
    def __init__(self, parent):
        self.parent = parent
    def fill_and_validate(self, data:dict, error_counter:ErrorCounter):
        def verify_source(path):
            if not os.path.isdir(os.path.join(path, ".git")):
                return "the directory '%s' must be a git repository" % path
            else:
                return None

        if data is None:
            error_counter.record("record-build section is empty")
        else:
            self.source = self.parent.check_mandatory_field(data, "source", verify_source, error_counter)
            self.max_days = self.parent.check_int_field(data, "max_days", 30, error_counter)
        
    def to_command(self):
        a = ("launchable", "record", "build", "--name", self.parent.eval_build_id(), "--source", self.source)
        if self.max_days != 30:
            a += ("--max-days", str(self.max_days))
        return a

    @classmethod
    def auto_configure(cls, parent, path:str) -> "RecordBuildArgs":
        a = RecordBuildArgs(parent)
        a.source = "."
        a.max_days = 30
        return a
