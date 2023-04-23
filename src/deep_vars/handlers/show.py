from typing import Any

from ._base import DeepVarsHandler


class DeepVarsHandlerShow(DeepVarsHandler):
    """
    Base handler class for `DeepVars` for objects that are shown unchanged.
    """

    def process_obj(self, obj: Any, deep_vars_args: dict[str, Any]) -> Any:
        """
        Return `DeepVars` representation of `obj`.
        """
        return obj
