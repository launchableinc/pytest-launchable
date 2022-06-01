
class ErrorCounter:
    def __init__(self):
        self.error_count = 0
        self.error_messages = []

    def record(self, message: str):
        self.error_count += 1
        self.error_messages.append(message)

    def print_errors(self):
        print("total %d errors are found." % (self.error_count, ))
        for message in self.error_messages:
            print(message)
