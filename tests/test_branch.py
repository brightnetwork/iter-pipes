from iter_pipes.functional import filter, map
from iter_pipes.main import PipelineFactory


def minus(item: int) -> int:
    return -item


def to_str(item: int) -> str:
    return str(item)


class Add:
    def __init__(self, value: int):
        self.value = value

    def __call__(self, item: int) -> int:
        return item + self.value


def filter_multiples_of_3(item: int) -> bool:
    return item % 3 == 0


def test_inflight_balancing():
    max_inflight = 3
    p = (
        PipelineFactory[int]()
        .branch(
            lambda pipeline: pipeline  #
            | filter(filter_multiples_of_3)
            | map(to_str),
            lambda pipeline: pipeline  #
            | map(minus),
            max_inflight=max_inflight,
        )
        .process(range(12))
        .to_list()
    )
    assert p == ["0", 0, -1, -2, "3", -3, -4, -5, "6", -6, -7, -8, "9", -9, -10, -11]
