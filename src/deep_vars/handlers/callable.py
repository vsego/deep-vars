import inspect
from typing import Any

from ._base import DeepVarsHandler


class DeepVarsHandlerCallable(DeepVarsHandler):
    """
    Handler class for `DeepVars` for callable objects.
    """

    def process_obj(self, obj: Any, deep_vars_args: dict[str, Any]) -> Any:
        """
        Return `DeepVars` representation of `obj`.
        """
        if callable(obj):
            try:
                signature = inspect.signature(obj)
            except ValueError:
                return "<built-in function>"
            else:
                return f"{obj.__name__}{signature}"
        else:
            return self.deep_vars.error_object
