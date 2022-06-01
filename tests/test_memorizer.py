from pytest_launchable.memorizer import memorizer


class Test_Memorizer:
    @memorizer
    def body(self):
        self.call_count += 1
        return 100

    def test_memorize(self):
        self.call_count = 0
        a = self.body()
        b = self.body()
        assert a == 100
        assert b == 100
        assert self.call_count == 1, "must evaluate only once"
