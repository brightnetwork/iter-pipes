import pytest

from iter_pipes.main import PipelineFactory


def test_empty_step():
    with pytest.raises(ValueError):  # noqa
        PipelineFactory[int]().process()

    with pytest.raises(ValueError):  # noqa
        PipelineFactory[int]().map(lambda x: x).process()

    with pytest.raises(ValueError):  # noqa
        PipelineFactory[int]().process(range(10))
