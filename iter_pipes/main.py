from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterator
from typing import Any, Generic, Iterable, TypeGuard, TypeVar, overload

from iter_pipes.functional import (
    batch,
    branch,
    filter,
    flatten,
    for_batch,
    for_each,
    identity,
    map,
)

T_contra = TypeVar("T_contra", contravariant=True)
U_co = TypeVar("U_co", covariant=True)
V = TypeVar("V")
W = TypeVar("W")
X = TypeVar("X")
Y = TypeVar("Y")

__all__ = ["Pipeline", "PipelineFactory"]


raw_filter = filter


Step = Callable[[Iterable[T_contra]], Iterable[U_co]]


def compose_steps(
    step1: Step[T_contra, U_co] | None, step2: Step[U_co, V]
) -> Step[T_contra, V]:
    if step1 is None:
        return step2  # type: ignore

    def composed(items: Iterable[T_contra]) -> Iterable[V]:
        return step2(step1(items))

    return composed


class IterableWrapper(Generic[T_contra]):
    def __init__(self, iterable: Iterable[T_contra]):
        self._iterable = iterable

    def __iter__(self) -> Iterator[T_contra]:
        return iter(self._iterable)

    def consume(self) -> None:
        deque(self._iterable, maxlen=0)

    def to_list(self) -> list[T_contra]:
        return list(self._iterable)


class Pipeline(Generic[T_contra, U_co]):
    step: Step[T_contra, U_co] | None
    items: Iterable[T_contra] | None

    def __init__(
        self,
        step: Step[T_contra, U_co] | None = None,
        items: Iterable[T_contra] | None = None,
    ):
        self.step = step
        self.items = items

    def for_each(self, step: Callable[[U_co], Any]) -> Pipeline[T_contra, U_co]:
        return self | for_each(step)

    def map(self, step: Callable[[U_co], W]) -> Pipeline[T_contra, W]:
        return self | map(step)

    def pipe(self, step: Step[U_co, V]) -> Pipeline[T_contra, V]:
        return Pipeline(compose_steps(self.step, step), self.items)

    def for_batch(
        self, step: Callable[[list[U_co]], Any], batch_size: int
    ) -> Pipeline[T_contra, U_co]:
        return self | for_batch(step, batch_size)

    def batch(
        self, step: Callable[[list[U_co]], Iterable[V]], batch_size: int
    ) -> Pipeline[T_contra, V]:
        return self | batch(step, batch_size)

    @overload
    def filter(self, step: Callable[[U_co], TypeGuard[W]]) -> Pipeline[T_contra, W]: ...

    @overload
    def filter(self, step: Callable[[U_co], bool]) -> Pipeline[T_contra, U_co]: ...

    def filter(self, step):  # type: ignore
        return self | filter(step)  # type: ignore

    def filter_not_none(self: Pipeline[T_contra, X | None]) -> Pipeline[T_contra, X]:
        return self | filter(lambda item: item is not None)  # type: ignore

    def flatten(self: Pipeline[T_contra, Iterable[W]]) -> Pipeline[T_contra, W]:
        return self | flatten()

    @overload
    def branch(
        self,
        f1: Callable[[Pipeline[U_co, U_co]], Pipeline[U_co, W]],
        max_inflight: int = ...,
    ) -> Pipeline[U_co, W]: ...

    @overload
    def branch(
        self,
        f1: Callable[[Pipeline[U_co, U_co]], Pipeline[U_co, V]],
        f2: Callable[[Pipeline[U_co, U_co]], Pipeline[U_co, W]],
        max_inflight: int = ...,
    ) -> Pipeline[U_co, W | V]: ...

    @overload
    def branch(
        self,
        f1: Callable[[Pipeline[U_co, U_co]], Pipeline[U_co, V]],
        f2: Callable[[Pipeline[U_co, U_co]], Pipeline[U_co, W]],
        f3: Callable[[Pipeline[U_co, U_co]], Pipeline[U_co, X]],
        max_inflight: int = ...,
    ) -> Pipeline[U_co, W | V | X]: ...

    @overload
    def branch(  # W291
        self,
        f1: Callable[[Pipeline[U_co, U_co]], Pipeline[U_co, V]],
        f2: Callable[[Pipeline[U_co, U_co]], Pipeline[U_co, W]],
        f3: Callable[[Pipeline[U_co, U_co]], Pipeline[U_co, X]],
        f4: Callable[[Pipeline[U_co, U_co]], Pipeline[U_co, Y]],
        max_inflight: int = ...,
    ) -> Pipeline[U_co, W | V | X | Y]: ...

    def branch(  # type: ignore
        self,
        *functions: Callable[[Pipeline[U_co, U_co]], Pipeline[U_co, Any]],
        max_inflight: int = 1000,
    ) -> Pipeline[U_co, Any]:
        steps = [f(Pipeline()).step or identity for f in functions]
        return self | branch(*steps, max_inflight=max_inflight, pick_first=False)  # type: ignore

    def branch_off(
        self,
        *functions: Callable[[Pipeline[U_co, U_co]], Pipeline[U_co, Any]],
        max_inflight: int = 1000,
    ) -> Pipeline[T_contra, U_co]:
        steps = [f(Pipeline()).step or identity for f in functions]
        return self | branch(
            identity, *steps, max_inflight=max_inflight, pick_first=True
        )  # type: ignore

    def process(self, items: Iterable[T_contra] | None = None) -> IterableWrapper[U_co]:
        input_ = items or self.items
        if not input_:
            raise ValueError("input is None")
        if not self.step:
            raise ValueError("step is None")
        return IterableWrapper(self.step(input_))

    def __call__(
        self, items: Iterable[T_contra] | None = None
    ) -> IterableWrapper[U_co]:
        return self.process(items)

    def __or__(self, step: Step[U_co, V]) -> Pipeline[T_contra, V]:
        return self.pipe(step)


class PipelineFactory(Generic[V], Pipeline[V, V]):
    pass
