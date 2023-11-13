from iter_pipes.main import PipelineFactory


def minus(item: int) -> int:
    return -item


def to_str(item: int) -> str:
    return str(item)


def test_main():
    p = (
        PipelineFactory[int]()  #
        .map(minus)
        .map(to_str)
        .process(range(10))
        .to_list()
    )

    assert p == ["0", "-1", "-2", "-3", "-4", "-5", "-6", "-7", "-8", "-9"]
