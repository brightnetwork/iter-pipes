from iter_pipes import PipelineFactory


def even_or_none(item: int) -> int | None:
    return item if item % 2 == 0 else None


def test_consume():
    queue = set()
    (
        PipelineFactory[int]()
        .map(even_or_none)
        .filter_not_none()
        .for_each(lambda item: queue.add(item))
        .process(range(10))
        .consume()
    )
    assert queue == {0, 2, 4, 6, 8}
