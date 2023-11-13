from functools import reduce

from iter_pipes.main import PipelineFactory

# you can use process events by batches
# especially useful to batch db requests / network calls


class ToStr:
    def __call__(self, item: int) -> str:
        return str(item)


class MultiplyTogether:
    def __call__(self, items: list[int]) -> list[int]:
        return [reduce(lambda x, y: x * y, items, 1) for _ in items]


def test_main():
    p = (
        PipelineFactory[int]()  #
        .batch(MultiplyTogether(), batch_size=3)
        .map(ToStr())
        .process(range(10))
        .to_list()
    )

    assert p == ["0", "0", "0", "60", "60", "60", "336", "336", "336", "9"]
