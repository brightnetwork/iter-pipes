from iter_pipes.main import PipelineFactory


def minus(item: int) -> int:
    return -item


def lte_4(item: int) -> bool:
    return item <= 4


class Add:
    def __init__(self, value: int):
        self.value = value

    def __call__(self, item: int) -> int:
        return item + self.value


def test_main():
    p = (
        PipelineFactory[int]()  #
        .map(minus)
        .branch(
            lambda pipeline: pipeline.map(Add(1)),
            lambda pipeline: pipeline.map(Add(2)).map(minus).filter(lte_4),
        )
        .process(range(9))
        .to_list()
    )

    assert p == [1, -2, 0, -1, -1, 0, -2, 1, -3, 2, -4, 3, -5, 4, -6, -7]
