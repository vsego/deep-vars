from typing import Any

from ._container import DeepVarsHandlerContainer


class DeepVarsHandlerLoop(DeepVarsHandlerContainer):
    """
    Base handler class for `DeepVars` for objects that are shown unchanged.
    """

    def process_obj(self, obj: Any, deep_vars_args: dict[str, Any]) -> Any:
        """
        Return `DeepVars` representation of `obj`.
        """
        if isinstance(obj, set):
            try:
                return {
                    self.deep_vars.deep_vars(value, **deep_vars_args)
                    for value in obj
                    if self.use_subobj(None, value, deep_vars_args)
                }
            except TypeError:
                # DeepVars subobjects cannot all be hashed, so we'll fall back
                # to unprocessed `obj`.
                return obj
        return_type: type[tuple] | type[list] = (
            tuple if isinstance(obj, tuple) else list
        )
        return return_type(
            self.deep_vars.deep_vars(value, **deep_vars_args)
            for value in obj
            if self.use_subobj(None, value, deep_vars_args)
        )
