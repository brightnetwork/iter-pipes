from iter_pipes.main import PipelineFactory


def minus(item: int) -> int:
    return -item


class Add:
    def __init__(self, value: int):
        self.value = value

    def __call__(self, item: int) -> int:
        return item + self.value


def join(item: tuple[int | None, int | None]) -> str:
    return f"{item[0]}:{item[1]}"


def to_str(item: int) -> str:
    return str(item)


def test_main():
    p = (
        PipelineFactory[int]()  #
        .map(minus)
        .branch(
            lambda pipeline: pipeline.map(Add(1)),
            lambda pipeline: pipeline.map(Add(2)).map(minus),
        )
        .process(range(10))
        .to_list()
    )

    assert p == [1, -2, 0, -1, -1, 0, -2, 1, -3, 2, -4, 3, -5, 4, -6, 5, -7, 6, -8, 7]
