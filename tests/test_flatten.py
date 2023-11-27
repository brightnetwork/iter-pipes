from iter_pipes import PipelineFactory


def test_consume():
    result = (
        PipelineFactory[int]()  #
        .map(lambda x: range(x))
        .flatten()
        .process(range(5))
        .to_list()
    )
    assert result == [0, 0, 1, 0, 1, 2, 0, 1, 2, 3]
