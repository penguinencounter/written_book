from typing import Tuple, TypeAlias

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None
IsInstanceType: TypeAlias = type | Tuple[type]
