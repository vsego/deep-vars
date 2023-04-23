from typing import Any, ClassVar

from ._container import DeepVarsHandlerContainer


class DeepVarsHandlerLoopDict(DeepVarsHandlerContainer):
    """
    Handler class for `DeepVars` for `dict`-like objects.
    """

    items_method_name: ClassVar[str] = "items"
    items_method_args: ClassVar[tuple[Any, ...]] = tuple()
    items_method_kwargs: ClassVar[dict[str, Any]] = dict()

    def process_obj(self, obj: Any, deep_vars_args: dict[str, Any]) -> Any:
        """
        Return `DeepVars` representation of `obj`.
        """
        return {
            name: self.deep_vars.deep_vars(value, **deep_vars_args)
            for name, value in getattr(obj, self.items_method_name)(
                *self.items_method_args, **self.items_method_kwargs,
            )
            if self.use_subobj(name, value, deep_vars_args)
        }
