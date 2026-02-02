"""
mares: mark's result class for safe value retrieval
  with all my heart, 2023-2026, mark joshwel <mark@joshwel.co>
  SPDX-License-Identifier: Unlicense OR 0BSD
"""

from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from sys import argv, stderr, stdin, stdout
from typing import Callable, Generic, NoReturn, ParamSpec, TypeVar, cast

__VERSION__ = "2026.2.3"


T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")
U = TypeVar("U")


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

    usage:
        ```python
        # do something
        def wrapped_read(path: str) -> Result[str]:
            try:
                with open(path, encoding="utf-8") as file:
                    contents = file.read()
            except Exception as exc:
                # must pass a default value
                return Result[str]("", error=exc)
            else:
                return Result[str](contents)

        # call function and handle result
        # and check if the result is erroneous
        result = wrapped_read("some_file.txt")

        if not result:
            # .cry() raises the exception
            # (or returns it as a string error message using string=True)
            print(f"error: {result.cry()}")
            exit()
        else:
            # .get() raises exception or returns value,
            # but since we checked for errors this is safe
            print(result.get())

        # railway-oriented example
        def parse_int(text: str) -> Result[int]:
            try:
                return Result[int](int(text.strip()))
            except ValueError as exc:
                return Result[int](0, error=exc)

        chained = (
            wrapped_read("some_file.txt")
            .bind(parse_int)
            .map(lambda value: value * 2)
        )

        if not chained:
            print(f"error: {chained.cry()}")
        else:
            print(chained.get())
        ```
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


def _result_snippet() -> str:
    lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    snippet_lines = lines[15:186]
    return "\n".join(snippet_lines)


def _add_imports(lines: list[str]) -> list[str]:
    required = [
        "from dataclasses import dataclass",
        "from functools import wraps",
        "from typing import Callable, Generic, ParamSpec, TypeVar, cast",
    ]
    missing = [line for line in required if line not in lines]
    if not missing:
        return lines
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    while insert_at < len(lines) and lines[insert_at].startswith(
        "from __future__ import"
    ):
        insert_at += 1
    updated = lines[:insert_at] + missing + [""] + lines[insert_at:]
    return updated


def _replace_marker(text: str, snippet: str) -> str:
    lines: list[str] = text.splitlines()
    marker_index = next(
        (
            current_index
            for current_index, line in enumerate(lines)
            if line == "# mares"
        ),
        None,
    )

    if marker_index is None:
        _die("mares: error: could not find a '# mares' marker to replace code with")

    lines[marker_index : marker_index + 1] = snippet.splitlines()

    output = "\n".join(lines)
    if text.endswith("\n"):
        output += "\n"
    return output


CLI_HELP = """mares: cli insertion tool for mark's result class for safe value retrieval

usage:
    mares insert [<path>] [--dont-import] [--read-from-stdin] [--write-to-stdout]
    mares insert --read-from-stdin <path> [--dont-import]
    mares insert --write-to-stdout [--dont-import]
    mares --help
    mares --version

note: replaces a line exactly matching "# mares"
note: --write-to-stdout with no path prints the Result code block
"""


def _print_help() -> None:
    _ = stdout.write(CLI_HELP)


def _die(message: str | None = None) -> NoReturn:
    if message:
        print(message, file=stderr)
    raise SystemExit(1)


def cli() -> None:
    args: list[str] = argv[1:]
    if not args:
        print("mares: error: missing command\n", file=stderr)
        _print_help()
        _die()

    if "--version" in args or "-V" in args:
        _ = stdout.write(f"{__VERSION__}\n")
        return

    if args[0] in {"--help", "-h"}:
        _print_help()
        return

    command = args[0]
    if command != "insert":
        _die(f"mares: error: unknown command {command}")

    if "--help" in args[1:] or "-h" in args[1:]:
        _print_help()
        return

    flags: set[str] = set()
    positionals: list[str] = []
    for item in args[1:]:
        if item in {"--dont-import", "--read-from-stdin", "--write-to-stdout"}:
            flags.add(item)
        elif item.startswith("--"):
            _die(f"mares: error: unknown option {item}")
        else:
            positionals.append(item)

    if len(positionals) > 1:
        _die("mares: error: too many arguments")

    path: Path | None = Path(positionals[0]) if positionals else None
    read_from_stdin: bool = "--read-from-stdin" in flags
    write_to_stdout: bool = "--write-to-stdout" in flags
    dont_import: bool = "--dont-import" in flags

    if path is None and not read_from_stdin and not write_to_stdout:
        _die("mares: error: missing path to insert into")

    snippet: str = _result_snippet()
    if path is None and write_to_stdout and not read_from_stdin:
        snippet_lines = snippet.splitlines()
        if not dont_import:
            snippet_lines = _add_imports(snippet_lines)
        output_text = "\n".join(snippet_lines)
        if snippet.endswith("\n"):
            output_text += "\n"
        _ = stdout.write(output_text)
        return

    if read_from_stdin:
        original: str = stdin.read()
    else:
        if path is None:
            _die("mares: error: missing path to insert into")
        original = path.read_text(encoding="utf-8")

    replaced: str = _replace_marker(original, snippet)
    lines: list[str] = replaced.splitlines()

    if not dont_import:
        lines = _add_imports(lines)

    output: str = "\n".join(lines)
    if replaced.endswith("\n"):
        output += "\n"

    if write_to_stdout:
        _ = stdout.write(output)
        return

    if path is None:
        _die("mares: error: missing path to write output to")
    _ = path.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    cli()
