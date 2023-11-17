[![image](https://img.shields.io/pypi/v/iter-pipes.svg)](https://pypi.python.org/pypi/iter-pipes)
[![image](https://img.shields.io/pypi/l/iter-pipes.svg)](https://pypi.python.org/pypi/iter-pipes)
[![image](https://img.shields.io/pypi/pyversions/iter-pipes.svg)](https://pypi.python.org/pypi/iter-pipes)
[![Code Coverage](https://img.shields.io/codecov/c/github/brightnetwork/iter-pipes)](https://app.codecov.io/gh/brightnetwork/iter-pipes)
[![Actions status](https://github.com/brightnetwork/iter-pipes/workflows/test/badge.svg)](https://github.com/brightnetwork/iter-pipes/actions)

## `iter_pipes`: Iterable Pipes

Functional pythonic pipelines for iterables.


```bash
pip install git+https://github.com/brightnetwork/iter-pipes
```

### Examples

#### map / filter:

```python
import math

from iter_pipes import PipelineFactory

pipeline = (
    PipelineFactory[int]()
    .map(math.exp)
    .filter(lambda x: x > math.exp(2))
    .map(math.log)
    .map(str)
)

assert pipeline(range(5)).to_list() == ["3.0", "4.0"]
```

#### Batch operations

```python
def get_user_names_from_db(user_ids: list[int]) -> list[str]:
    # typical batch operation:
    #   - duration is roughly constant for a batch
    #   - batch size has to be below a fixed threshold
    print("processing batch", user_ids)
    return [f"user_{user_id}" for user_id in user_ids]


pipeline = (
    PipelineFactory[int]()
    .batch(get_user_names_from_db, batch_size=3)
    .for_each(lambda user_name: print("Hello ", user_name))
)

pipeline(range(5)).to_list()
# returns
#   ["user_0", "user_1", "user_2", "user_3", "user_4"]
# prints
#   processing batch [0, 1, 2]
#   Hello  user_0
#   Hello  user_1
#   Hello  user_2
#   processing batch [3, 4]
#   Hello  user_3
#   Hello  user_4
```


#### Storing state

Class with a `__call__` method provide a easy way to store a state during the processing.

```python
class CountUsers:
    def __init__(self):
        self._count = 0

    def __call__(self, item: str) -> str:
        self._count += 1
        return f"{item} (position {self._count})"


pipeline = PipelineFactory[int]().map(lambda x: f"user {x}").map(CountUsers())

pipeline.process(range(5)).to_list()
# return
#    ['user 0 (position 1)', 'user 1 (position 2)', 'user 2 (position 3)', 'user 3 (position 4)', 'user 4 (position 5)']
```

One could also use a closure:

```python
def count_users():
    count = 0

    def wrapper(item: str) -> str:
        nonlocal count
        count += 1
        return f"{item} (position {count})"

    return wrapper


pipeline = PipelineFactory[int]().map(lambda x: f"user {x}").map(count_users())

pipeline.process(range(5)).to_list()
# return
#    ['user 0 (position 1)', 'user 1 (position 2)', 'user 2 (position 3)', 'user 3 (position 4)', 'user 4 (position 5)']
```

#### Branches

```python
pipeline = (
    PipelineFactory[int]()
    .branch(
        lambda x: x.filter(lambda x: x % 2 == 0).map(lambda x: x**2),
        lambda x: x.map(lambda x: -x),
    )
    .map(str)
)

expected = ["0", "0", "4", "-1", "-2", "16", "-3", "-4", "36", "-5", "-6", "-7"]
assert pipeline(range(8)).to_list() == expected
```

Each "branch" order will be preserved, but there is not guarantee in term of how the two are merged.

There is also `branch_off` which discard the output of the branch:

```python
pipeline = (
    PipelineFactory[int]()
    .branch_off(
        lambda x: x.filter(lambda x: x % 2 == 0).map(lambda x: x**2),
    )
    .map(str)
)

expected = ["0", "0", "4", "16", "36"]
assert pipeline(range(8)).to_list() == expected
```

#### Pipe operator overload

```python
import iter_pipes.functional as itp

pipeline = (
    PipelineFactory[int]()
    | itp.map(math.exp)
    | itp.filter(lambda x: x > math.exp(2))  # type checker might complain
    | itp.map(math.log)
    | itp.map(str)
)

assert pipeline(range(6)).to_list() == ["3.0", "4.0", "5.0"]
```

note that typing of lambda function inside functional map is not as good as the one from the `Pipeline.XXX` methods. To work around this, one should either use the non functional style, either use fully typed function instead of lambda.


#### Resumability

```python
pipeline = PipelineFactory[int]().branch(
    lambda x: x.filter(lambda x: x % 3 == 0).map(str),
    lambda x: x,
)

print(pipeline.process(range(12)).to_list())
# return
#    ['0', 0, '3', 1, 2, 3, '6', 4, 5, 6, '9', 7, 8, 9, 10, 11]
# note that between each yield from the first branch, the pipeline will yield everything
# from the second branch so that we don't store too many messages in the inflight buffer.


def filter_out_everything(items: Iterable[int]) -> Iterable[int]:
    print("starting")
    for item in items:
        if False:
            yield item


pipeline = PipelineFactory[int]().branch(
    lambda x: x.pipe(filter_out_everything).map(str),
    lambda x: x,
    max_inflight=5,
)

print(pipeline.process(range(9)).to_list())
# return
#    [0, 1, 2, 3, 4, 5, 6, 7, 8]
# print
#    starting
#    starting
#    starting
```

### Motivations

Goal of the library is to provide a structure to work with [collection pipelines](https://martinfowler.com/articles/collection-pipeline/).

> Collection pipelines are a programming pattern where you organize some computation as a sequence of operations which compose by taking a collection as output of one operation and feeding it into the next. 

In this library, each "operation" is called a "step". We differentiate different subtype for steps:
- `map` steps will operate on each item of the collection, one by one
- `filter` steps will reduce the number of item in the collection, without changing their values
- `for_each` steps will do some processing, but without impacting the following steps (they won't change the input)
- `batch` steps will operate by batch of a fixed size - can be useful for example to batch database calls.

In addition to that, we also define pipeline `branch`, which allow to run several steps after a single one.

Library goal:
- declarative, expressive syntax for the steps above
- memory efficiency:
    - pure python, so it's not optimal at all
    - but what we care about is ensuring that the memory used by the pipeline does not scale with the number of items in the collection.
- performant:
    - pure python, so the code itself is not really performant
    - but the library allow for an optimal usage of the "slow" operations (network calls mainly) that are computed in the pipeline. This is what is meant by "performant"
- lightweight usage, as in existing function can be used as a step without the need for a wrapper
- provide as good of a type experience as possible



### Documentation

Have a look at the [`docs`](./tests/docs/) part of the test suites for examples.

### Contributing

Please refer to the [`test`](./.github/workflows/test.yml) actions. 100% test coverage is a start.
