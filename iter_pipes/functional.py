from __future__ import annotations

import math
from collections import deque
from collections.abc import Callable, Iterable, Iterator
from functools import partial
from itertools import count, groupby
from typing import Any, Literal, TypeGuard, TypeVar, overload

__all__ = [
    "map",
    "filter",
    "for_each",
    "for_batch",
    "batch",
    "branch",
]

T = TypeVar("T")
V = TypeVar("V")
U = TypeVar("U")
W = TypeVar("W")
X = TypeVar("X")


raw_filter = filter


Step = Callable[[Iterable[T]], Iterable[V]]


def flatten() -> Step[Iterable[T], T]:
    def f(data: Iterable[Iterable[T]]) -> Iterable[T]:
        for x in data:
            yield from x

    return f


def map(step: Callable[[V], W]) -> Step[V, W]:
    def f(data: Iterable[V]) -> Iterable[W]:
        for item in data:
            yield step(item)

    return f


def for_each(step: Callable[[V], Any]) -> Step[V, V]:
    def f(data: Iterable[V]) -> Iterable[V]:
        for item in data:
            step(item)
            yield item

    return f


def for_batch(step: Callable[[list[V]], Any], batch_size: int) -> Step[V, V]:
    def f(data: Iterable[V]) -> Iterable[V]:
        for _, batch_iterator in groupby(
            zip(data, count()),
            key=lambda x: math.floor(x[1] / batch_size),
        ):
            batch = [x[0] for x in batch_iterator]
            step(batch)
            yield from batch

    return f


def batch(step: Callable[[list[V]], Iterable[U]], batch_size: int) -> Step[V, U]:
    def f(data: Iterable[V]) -> Iterable[U]:
        for _, batch_iterator in groupby(
            zip(data, count()),
            key=lambda x: math.floor(x[1] / batch_size),
        ):
            yield from step([x[0] for x in batch_iterator])

    return f


@overload
def filter(step: Callable[[V], TypeGuard[W]]) -> Step[V, W]:
    ...


@overload
def filter(step: Callable[[V], bool]) -> Step[V, V]:
    ...


def filter(step: Callable[[V], bool]) -> Step[V, V]:  # type: ignore
    return partial(raw_filter, step)  # type: ignore


@overload
def branch(
    step1: Step[T, U] | None,
    step2: Step[T, V],
    pick_first: Literal[True],
    max_inflight: int | None = ...,
) -> Step[T, U]:
    ...


@overload
def branch(
    step1: Step[T, U],
    step2: Step[T, V],
    pick_first: Literal[False] | None,
    max_inflight: int | None = ...,
) -> Step[T, V | U]:
    ...


@overload
def branch(
    step1: Step[T, U],
    step2: Step[T, V],
    step3: Step[T, W],
    pick_first: Literal[False] | None,
    max_inflight: int | None = ...,
) -> Step[T, V | U | W]:
    ...


@overload
def branch(  # noqa: PLR0913
    step1: Step[T, U],
    step2: Step[T, V],
    step3: Step[T, W],
    step4: Step[T, X],
    pick_first: Literal[False] | None,
    max_inflight: int | None = ...,
) -> Step[T, V | U | W | X]:
    ...


@overload
def branch(
    *steps: Step[T, Any] | None,
    pick_first: Literal[False] | None,
    max_inflight: int | None = ...,
) -> Step[T, Any]:
    ...


def branch(  # type: ignore
    *steps: Step[T, Any] | None,
    max_inflight: int = 1000,
    pick_first: bool = False,
) -> Step[T, Any]:
    """
    Returns a step that forks the input iterable into multiple iterables,
    each one being processed by a different step. The output iterable is the
    concatenation of the output of each step.

    If `pick_first` is True, the output iterable is the concatenation of the
    output of the first step only.
    """

    def wrapper(iterable: Iterable[T]) -> Iterable[Any]:
        it = iter(iterable)

        queues: list[deque[T]] = [deque() for _ in steps]
        # could be rewritten with a single deque to be more memory efficient

        # the set of iterators that are paused because we have too many inflight items
        # they should be resumed when the number of inflight items goes down
        paused_iterators: set[int] = set()

        def gen(i: int) -> Iterator[T]:
            while True:
                mydeque = queues[i]
                if not mydeque:  # when the current deque is empty
                    try:
                        newval = next(it)  # fetch a new value and
                    except StopIteration:
                        return
                    for d in queues:  # load it to all the deques
                        d.append(newval)

                    # if there are too many inflight items, pause the iterator
                    nb_inflights = sum(len(q) for q in queues)
                    if nb_inflights > max_inflight:
                        paused_iterators.add(i)
                        return

                yield mydeque.popleft()

        iterators = [iter((steps[i] or identity)(gen(i))) for i in range(len(steps))]

        # the set of iterators that are not done yet
        pending_iterators = set(range(len(iterators)))

        while len(pending_iterators):
            i = max(  # the index of the iterator with the most inflight items
                pending_iterators,
                key=lambda i: len(queues[i]),
            )
            try:
                val = next(iterators[i])
                if not pick_first or i == 0:
                    yield val
            except StopIteration:
                if i in paused_iterators:  # resume the iterator
                    iterators[i] = iter((steps[i] or identity)(gen(i)))
                    paused_iterators.remove(i)
                else:
                    pending_iterators.remove(i)

    return wrapper


def identity(item: W) -> W:
    return item
