from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterator
from typing import Any, Generic, Iterable, TypeGuard, TypeVar, overload

from iter_pipes.functional import (
    batch,
    branch,
    filter,
    for_batch,
    for_each,
    identity,
    map,
)

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")
W = TypeVar("W")
X = TypeVar("X")
Y = TypeVar("Y")

__all__ = ["Pipeline", "PipelineFactory"]


raw_filter = filter


Step = Callable[[Iterable[T]], Iterable[U]]


def compose_steps(step1: Step[T, U] | None, step2: Step[U, V]) -> Step[T, V]:
    if step1 is None:
        return step2  # type: ignore

    def composed(items: Iterable[T]) -> Iterable[V]:
        return step2(step1(items))

    return composed


class IterableWrapper(Generic[T]):
    def __init__(self, iterable: Iterable[T]):
        self._iterable = iterable

    def __iter__(self) -> Iterator[T]:
        return iter(self._iterable)

    def consume(self) -> None:
        deque(self._iterable)

    def to_list(self) -> list[T]:
        return list(self._iterable)


class Pipeline(Generic[T, U]):
    step: Step[T, U] | None
    items: Iterable[T] | None

    def __init__(
        self,
        step: Step[T, U] | None = None,
        items: Iterable[T] | None = None,
    ):
        self.step = step
        self.items = items

    def for_each(self, step: Callable[[U], Any]) -> Pipeline[T, U]:
        return self | for_each(step)

    def map(self, step: Callable[[U], W]) -> Pipeline[T, W]:
        return self | map(step)

    def pipe(self, step: Step[U, V]) -> Pipeline[T, V]:
        return Pipeline(compose_steps(self.step, step), self.items)

    def for_batch(
        self, step: Callable[[list[U]], Any], batch_size: int
    ) -> Pipeline[T, U]:
        return self | for_batch(step, batch_size)

    def batch(
        self, step: Callable[[list[U]], Iterable[V]], batch_size: int
    ) -> Pipeline[T, V]:
        return self | batch(step, batch_size)

    @overload
    def filter(self, step: Callable[[U], TypeGuard[W]]) -> Pipeline[T, W]:
        ...

    @overload
    def filter(self, step: Callable[[U], bool]) -> Pipeline[T, U]:
        ...

    def filter(self, step):  # type: ignore
        return self | filter(step)  # type: ignore

    def filter_not_none(self: Pipeline[T, X | None]) -> Pipeline[T, X]:
        return self | filter(lambda item: item is not None)  # type: ignore

    @overload
    def branch(
        self,
        f1: Callable[[Pipeline[U, U]], Pipeline[U, W]],
        max_inflight: int = ...,
    ) -> Pipeline[U, W]:
        ...

    @overload
    def branch(
        self,
        f1: Callable[[Pipeline[U, U]], Pipeline[U, V]],
        f2: Callable[[Pipeline[U, U]], Pipeline[U, W]],
        max_inflight: int = ...,
    ) -> Pipeline[U, W | V]:
        ...

    @overload
    def branch(
        self,
        f1: Callable[[Pipeline[U, U]], Pipeline[U, V]],
        f2: Callable[[Pipeline[U, U]], Pipeline[U, W]],
        f3: Callable[[Pipeline[U, U]], Pipeline[U, X]],
        max_inflight: int = ...,
    ) -> Pipeline[U, W | V | X]:
        ...

    @overload
    def branch(  # noqa W291
        self,
        f1: Callable[[Pipeline[U, U]], Pipeline[U, V]],
        f2: Callable[[Pipeline[U, U]], Pipeline[U, W]],
        f3: Callable[[Pipeline[U, U]], Pipeline[U, X]],
        f4: Callable[[Pipeline[U, U]], Pipeline[U, Y]],
        max_inflight: int = ...,
    ) -> Pipeline[U, W | V | X | Y]:
        ...

    def branch(  # type: ignore
        self,
        *functions: Callable[[Pipeline[U, U]], Pipeline[U, Any]],
        max_inflight: int = 1000,
    ) -> Pipeline[U, Any]:
        steps = [f(Pipeline()).step or identity for f in functions]
        return self | branch(*steps, max_inflight=max_inflight, pick_first=False)  # type: ignore

    def branch_off(
        self,
        *functions: Callable[[Pipeline[U, U]], Pipeline[U, Any]],
        max_inflight: int = 1000,
    ) -> Pipeline[T, U]:
        steps = [f(Pipeline()).step or identity for f in functions]
        return self | branch(
            identity, *steps, max_inflight=max_inflight, pick_first=True
        )  # type: ignore

    def process(self, items: Iterable[T] | None = None) -> IterableWrapper[U]:
        input_ = items or self.items
        if not input_:
            raise ValueError("input is None")
        if not self.step:
            raise ValueError("step is None")
        return IterableWrapper(self.step(input_))

    def __call__(self, items: Iterable[T] | None = None) -> IterableWrapper[U]:
        return self.process(items)

    def __or__(self, step: Step[U, V]) -> Pipeline[T, V]:
        return self.pipe(step)


class PipelineFactory(Generic[V], Pipeline[V, V]):
    pass
