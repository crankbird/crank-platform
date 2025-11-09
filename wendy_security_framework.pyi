from typing import Any


class SecurityViolation(Exception):
    ...


class WendyInputSanitizer:
    def __init__(self) -> None: ...
    def sanitize_filename(self, filename: str, service_type: str = ...) -> str: ...
    def sanitize_json_input(
        self,
        data: Any,
        max_depth: int | None = ...,
        current_depth: int = ...,
    ) -> Any: ...
