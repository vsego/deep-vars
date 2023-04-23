from typing import ClassVar, Any, Optional

from ._base import DeepVarsHandler


class DeepVarsHandlerContainer(DeepVarsHandler):
    """
    Base handler class for `DeepVars` for container objects.

    Do not use directly.
    """

    allow_filtering: ClassVar[bool] = False

    def use_subobj(
        self, name: Optional[str], value: Any, deep_vars_args: dict[str, Any],
    ) -> bool:
        return (
            not self.allow_filtering
            or self.deep_vars.use_obj(name, value, deep_vars_args)
        )
