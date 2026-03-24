# mares

**ma**rk's **res**ult class for safe data retrieval

or, as i learnt from opus 4.5, a railway-oriented two-track result pattern for 
explicit success/failure handling

- [the class](#the-class)
- [an example](#an-example)

## the class

```python
@dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    """
    `dataclasses.dataclass` representing a result for safe value retrieval

    attributes:
        `value: T`
            value to return or fallback value if erroneous
        `error: BaseException | None = None`
            exception if any

    methods:
        `def __bool__(self) -> bool: ...`
            method for boolean comparison for exception safety
        `def get(self) -> T: ...`
            method that raises or returns an error if the Result is erroneous
        `def map(self, func: Callable[[T], U]) -> Result[U]: ...`
            method that maps the value when not erroneous
        `def bind(self, func: Callable[[T], Result[U]]) -> Result[U]: ...`
            method that binds to another Result-returning function
        `def cry(self, string: bool = False) -> str: ...`
            method that returns the result value or raises an error
    """

    value: T
    error: BaseException | None = None

    def __bool__(self) -> bool:
        """
        method for boolean comparison for easier exception handling

        returns: `bool`
            that returns True if `self.error` is not None
        """
        return self.error is None

    def cry(self, string: bool = False) -> str:  # noqa: FBT001, FBT002
        """
        method that raises or returns an error if the Result is erroneous

        arguments:
            `string: bool = False`
                if `self.error` is an Exception, returns it as a string
                error message

        returns: `str`
            returns `self.error` as a string if `string` is True,
            or returns an empty string if `self.error` is None
        """

        if isinstance(self.error, BaseException):
            if string:
                message = f"{self.error}"
                name = self.error.__class__.__name__
                return f"{message} ({name})" if (message != "") else name

            raise self.error

        return ""

    def get(self) -> T:
        """
        method that returns the result value or raises an error

        returns: `T`
            returns `self.value` if `self.error` is None

        raises: `BaseException`
            if `self.error` is not None
        """
        if self.error is not None:
            raise self.error
        return self.value

    def map(self, func: Callable[[T], U]) -> "Result[U]":
        """
        method that maps the value when not erroneous

        arguments:
            `func: Callable[[T], U]`
                function to transform the value

        returns: `Result[U]`
            returns a new Result with the transformed value, or the same error
        """
        if self.error is not None:
            return Result(cast(U, self.value), error=self.error)
        return Result(func(self.value))

    def bind(self, func: Callable[[T], "Result[U]"]) -> "Result[U]":
        """
        method that binds to another Result-returning function

        arguments:
            `func: Callable[[T], Result[U]]`
                function to transform the value into a Result

        returns: `Result[U]`
            returns the bound Result, or the same error
        """
        if self.error is not None:
            return Result(cast(U, self.value), error=self.error)
        return func(self.value)

    @staticmethod
    def wrap(default: R) -> Callable[[Callable[P, R]], Callable[P, "Result[R]"]]:
        """decorator that wraps a non-Result-returning function to return a Result"""

        def result_decorator(func: Callable[P, R]) -> Callable[P, Result[R]]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[R]:
                try:
                    return Result(func(*args, **kwargs))
                except Exception as exc:
                    return Result(default, error=exc)

            return wrapper

        return result_decorator
```

## an example

```python
def fetch_json(url: str) -> Result[dict[str, Any]]:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = response.read().decode("utf-8")
        return Result(json.loads(data))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return Result({}, error=exc)

def require_field(data: dict[str, Any], field: str) -> Result[dict[str, Any]]:
    if field not in data:
        return Result({}, error=KeyError(f"Missing field: {field}"))
    return Result(data)

return (
    fetch_json(f"https://jsonplaceholder.typicode.com/users/{randint(1, 10)}")
    .bind(lambda payload: require_field(payload, "name"))
    .map(lambda payload: str(payload["name"]))
)
```

**bonus!** this is available as a library, and as a quick insertion tool.

```
pip install mares

uv add mares

uvx mares inject path/to/file.py
```
