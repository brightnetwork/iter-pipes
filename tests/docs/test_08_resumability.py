from iter_pipes.functional import filter
from iter_pipes.main import PipelineFactory

# resumability:
# when the steps change the size of the iterables in a branch, it's
# tricky to avoid memory leaks.
# for example, if a branch is having a filter that filters out all the items,
# the branch will consume all the messages without ever releasing the thread to
# the main pipeline. The messages will be stored in the inflights buffer for the
# main pipeline, and the main pipeline will never be able to consume them.
#
# The solution is to have a max_inflight parameter that will limit the number of
# inflight messages. When the number of inflight messages reaches the limit, the
# branch will be "paused" to let the main pipeline consume some messages.
# The branch will then be "resumed".
#
# The "pause" and "resume" behavior is implemented by stopping the branch
# source iterator, and then re-applying the branch steps to the source iterator


def minus(item: int) -> int:
    return -item


class Add:
    def __init__(self, value: int):
        self.value = value

    def __call__(self, item: int) -> int:
        return item + self.value


def join(item: tuple[int | None, int | None]) -> str:
    return f"{item[0]}:{item[1]}"


def counter():
    memory = set()

    def inc(x: int) -> None:
        memory.add(x)

    def dec(x: int) -> None:
        memory.remove(x)

    def get() -> int:
        return len(memory)

    return inc, dec, get


def return_false(_item: int) -> bool:
    return False


def test_main():
    max_inflight = 30
    inc, dec, get = counter()
    p = (
        PipelineFactory[int]()  #
        .for_each(inc)
        .branch_off(
            lambda pipeline: pipeline  #
            | filter(return_false),
            max_inflight=max_inflight,
        )
        .for_each(dec)
        .process(range(10**3))
    )
    result = []
    for x in p:
        assert get() <= max_inflight
        result.append(x)
    assert result == list(range(10**3))
