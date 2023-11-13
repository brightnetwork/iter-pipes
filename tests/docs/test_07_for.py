from iter_pipes.main import PipelineFactory

# `for` / `for_each` allow you to run functions at certain point of the
# pipeline, but ignore the return value


def minus(item: int) -> int:
    return -item


def to_str(item: int) -> str:
    return str(item)


def test_main():
    myset = set()

    def concatenate_and_print(items: list[int]) -> None:
        myset.add("".join([str(i) for i in items]))

    p = (
        PipelineFactory[int]()  #
        .map(minus)
        .for_each(to_str)
        .map(minus)  # still an iterable of int
        .for_batch(concatenate_and_print, batch_size=3)
        .map(to_str)
    )(range(10)).to_list()

    assert p == ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    assert myset == {"012", "345", "678", "9"}
