from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..deep_vars import DeepVars  # pragma: no cover


class DeepVarsInvalidHandlerError(NotImplementedError):
    """
    An error to catch if `process` below was not implemented.

    This allows any other `NotImplementedError` to pass through.
    """


class DeepVarsHandler:
    """
    Base handler class for `DeepVars`.

    Do not use directly.
    """

    def __init__(self, deep_vars: type["DeepVars"]) -> None:
        self.deep_vars = deep_vars

    @staticmethod
    def use_obj(obj: Any, deep_vars_args: dict[str, Any]) -> bool:
        """
        Return `True` if `obj` is to be used in `DeepVars` output.
        """
        return True

    def process(self, obj: Any, deep_vars_args: dict[str, Any]) -> Any:
        """
        Return `DeepVars` representation of `obj`.

        Do not override this. Instead, override :py:meth:`process`.
        """
        try:
            return self.process_obj(obj, deep_vars_args)
        except DeepVarsInvalidHandlerError:
            raise
        except Exception:
            return obj

    def process_obj(self, obj: Any, deep_vars_args: dict[str, Any]) -> Any:
        """
        Return `DeepVars` representation of `obj`.
        """
        raise DeepVarsInvalidHandlerError(
            f"don't use {type(self).__name__} directly",
        )
