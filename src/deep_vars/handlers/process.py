from typing import ClassVar, Any

from ._container import DeepVarsHandlerContainer


class DeepVarsHandlerProcess(DeepVarsHandlerContainer):
    """
    Base handler class for `DeepVars` for objects that are shown unchanged.
    """

    allow_filtering: ClassVar[bool] = True

    def get_sub_obj(self, obj: Any, name: str) -> Any:
        """
        Return `obj.name` or the error object.
        """
        try:
            return getattr(obj, name)
        except AttributeError:
            return self.deep_vars.error_object

    def process_obj(self, obj: Any, deep_vars_args: dict[str, Any]) -> Any:
        """
        Return `DeepVars` representation of `obj`.
        """
        return {
            name: self.deep_vars.deep_vars(
                value, _obj_name=name, **deep_vars_args,
            )
            for name, value in (
                (name, self.get_sub_obj(obj, name)) for name in dir(obj)
            )
            if self.use_subobj(name, value, deep_vars_args)
        }
