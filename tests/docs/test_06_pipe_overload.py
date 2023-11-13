import iter_pipes.functional as itp
from iter_pipes.main import PipelineFactory

# support the pipe operator (|) overload
# in particular, the auto-formating in branches is way prettier


def minus(item: int) -> int:
    return -item


def lte_4(item: int) -> bool:
    return item <= 4


def test_main():
    p = (
        PipelineFactory[int]()  #
        .map(minus)
        .branch(
            lambda pipeline: pipeline  #
            | itp.map(minus)
            | itp.filter(lte_4),
            lambda pipeline: pipeline  #
            | itp.map(minus)
            | itp.map(minus)
            | itp.filter(lte_4),
        )
        .process(range(9))
        .to_list()
    )

    assert p == [0, 0, 1, -1, 2, -2, 3, -3, 4, -4, -5, -6, -7, -8]
