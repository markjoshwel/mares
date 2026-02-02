import http.client
import json
import urllib.request
from random import randint
from typing import cast

from mares import Result


def fetch_user_name(url: str) -> Result[str]:
    def fetch_json(url: str) -> Result[dict[str, object]]:
        try:
            response = cast(
                http.client.HTTPResponse,
                urllib.request.urlopen(url, timeout=10),
            )
            data = response.read().decode("utf-8")
            payload = cast(object, json.loads(data))
            if not isinstance(payload, dict):
                return Result({}, error=ValueError("Expected a JSON object"))
            return Result(cast(dict[str, object], payload))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return Result({}, error=exc)

    def require_str_field(data: dict[str, object], field: str) -> Result[str]:
        value = data.get(field)
        if not isinstance(value, str):
            return Result("", error=KeyError(f"Missing or invalid field: {field}"))
        return Result(value)

    return fetch_json(url).bind(lambda payload: require_str_field(payload, "name"))


result = fetch_user_name(f"https://jsonplaceholder.typicode.com/users/{randint(1, 10)}")

if result:
    print(f"name: {result.value}")
if not result:
    print(result.error)
