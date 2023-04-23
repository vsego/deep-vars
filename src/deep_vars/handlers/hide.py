from typing import ClassVar, Optional, Any

from ._base import DeepVarsHandler
from .show import DeepVarsHandlerShow


class DeepVarsHandlerHide(DeepVarsHandler):
    """
    Base handler class for `DeepVars` for objects that are shown unchanged.
    """

    fallback_handler: ClassVar[Optional[type[DeepVarsHandler]]] = None

    @staticmethod
    def use_obj(obj: Any, deep_vars_args: dict[str, Any]) -> bool:
        """
        Return `True` if `obj` is to be used in `DeepVars` output.
        """
        return False

    def process_obj(self, obj: Any, deep_vars_args: dict[str, Any]) -> Any:
        """
        Return `DeepVars` representation of `obj`.
        """
        handler: DeepVarsHandler
        if self.fallback_handler is None:
            handler = self.deep_vars.get_handler(
                deep_vars_args.get("_obj_name"), obj,
            )
            if isinstance(handler, type(self)):
                handler = self.deep_vars.get_handler(None, obj)
        else:
            handler = self.deep_vars.get_handler_cache(self.fallback_handler)
        if isinstance(handler, type(self)):
            handler = self.deep_vars.get_handler_cache(DeepVarsHandlerShow)
        return handler.process(obj, deep_vars_args)
