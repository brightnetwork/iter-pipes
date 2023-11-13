from iter_pipes import PipelineFactory


def even_or_none(item: int) -> int | None:
    return item if item % 2 == 0 else None


def test_filter_typeguard():
    to_list = (
        PipelineFactory[int]()
        .map(even_or_none)
        .filter_not_none()
        .process(range(10))
        .to_list
    )
    _a: list[int] = to_list()  # type hinting removed the None
    assert _a == [0, 2, 4, 6, 8]
