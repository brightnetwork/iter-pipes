from iter_pipes.main import PipelineFactory

# you can use classes instead of functions
# this is useful for:
# - store state
# - dependency injection
# - break down complex logic into smaller pieces


class ToStr:
    def __call__(self, item: int) -> str:
        return str(item)


class Multiply:
    def __init__(self, value: int):
        self.value = value

    def __call__(self, item: int) -> int:
        return item * self.value


def test_main():
    p = (
        PipelineFactory[int]()  #
        .map(Multiply(-1))
        .map(ToStr())
    )(range(10)).to_list()

    assert p == ["0", "-1", "-2", "-3", "-4", "-5", "-6", "-7", "-8", "-9"]
