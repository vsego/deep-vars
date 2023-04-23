"""
Recursive `vars` for all objects.
"""

from collections.abc import Iterable
from copy import copy
from typing import TypeAlias, Optional, Any, Callable, ClassVar, cast
import uuid

from .handlers import (
    DeepVarsHandler, DeepVarsHandlerCallable, DeepVarsHandlerShow,
    DeepVarsHandlerHide, DeepVarsHandlerLoop, DeepVarsHandlerLoopDict,
    DeepVarsHandlerProcess, DeepVarsInvalidHandlerError,
)


class _DeepVarsErrorObject:
    """
    Class used when `dir` returns something that cannot be grabbed.
    """

    def __repr__(self):
        return "<<<ERROR>>>"


HandlerTypesT: TypeAlias = dict[type | str, type[DeepVarsHandler]]
HandlersT: TypeAlias = dict[type[DeepVarsHandler], DeepVarsHandler]
SpecialTypeDetectorT: TypeAlias = Callable[[Optional[str], Any], Optional[str]]
SpecialTypeDetectorsT: TypeAlias = list[SpecialTypeDetectorT]
BookmarksT: TypeAlias = dict[str, HandlerTypesT]


class DeepVars:
    """
    Recursive `vars` for all objects, including those not supporting `vars`.
    """

    error_object: ClassVar[Any] = _DeepVarsErrorObject()
    special_type_detectors: ClassVar[SpecialTypeDetectorsT] = list()
    default_handler: type[DeepVarsHandler] = DeepVarsHandlerProcess

    _handlers: ClassVar[HandlerTypesT] = {
        "magic": DeepVarsHandlerHide,
        "private": DeepVarsHandlerHide,
        "callable": DeepVarsHandlerCallable,
        int: DeepVarsHandlerShow,
        float: DeepVarsHandlerShow,
        str: DeepVarsHandlerShow,
        set: DeepVarsHandlerLoop,
        list: DeepVarsHandlerLoop,
        tuple: DeepVarsHandlerLoop,
        dict: DeepVarsHandlerLoopDict,
    }
    _handlers_cache: ClassVar[HandlersT] = dict()
    _bookmarks: ClassVar[BookmarksT] = dict()

    @classmethod
    def bookmark_handlers(cls, name: Optional[str] = None) -> str:
        """
        Set a bookmark with a given name for handlers.

        :param name: This can later be used to reference the bookmark, i.e., to
            reset the handlers to the state at which they were when this method
            was called. If the name is not given, a random one is assigned.
        :return: The name (either the given or the generated one).
        """
        if name is None:
            while True:
                name = str(uuid.uuid4())
                if name not in cls._bookmarks:
                    break
            name = cast(str, name)
        else:
            cls._bookmarks.pop(name, None)
        cls._bookmarks[name] = copy(cls._handlers)
        return name

    @classmethod
    def reset_handlers(
        cls, name: Optional[str] = None, delete: Optional[bool] = None,
    ) -> None:
        """
        Reset handlers to the ones defined by a bookmark.

        If `name` is not given, the last added bookmark is used and, if there
        is more than one bookmark in the collection of saved bookmarks, it is
        removed from the collection. If it is given, the bookmark with that
        name is used, but it is not removed from the collection.

        Notice that the first bookmark (containing the built-in defaults) is
        never removed and can always be reset using the following code:

        ```
        import deep_vars
        deep_vars.DeepVars.reset_handlers(deep_vars.DEFAULT_BOOKMARK)
        ```

        :param name: The name of the bookmark to be used.
        :param delete: Should the bookmark be deleted? If `None`, an
            "intelligent" approach is used: if the name is not given, the
            bookmark is deleted. This argument is ignored if there is only one
            bookmark in the collection)
        :raises KeyError: If `name` is not a valid one (i.e., there is no
            bookmark with that name).
        """
        if len(cls._bookmarks) <= 1:
            delete = False
        elif delete is None:
            delete = (name is None)
        if name is None:
            if delete:
                bookmark = cls._bookmarks.popitem()[1]
            else:
                bookmark = next(reversed(cls._bookmarks.values()))
        else:
            if delete:
                bookmark = cls._bookmarks.pop(name)
            else:
                bookmark = cls._bookmarks[name]

        cls._handlers.clear()
        cls._handlers.update(bookmark)

    @classmethod
    def clear_bookmarks(cls) -> None:
        """
        Delete all bookmarks (except the first one).

        This method only clears the bookmarks, but it does not change the
        current handlers. If you want to do a full reset (clear the bookmarks
        and reset the default settings), you also need to call
        :py:meth:`reset_handlers()`.
        """
        name = next(iter(cls._bookmarks))
        bookmark = cls._bookmarks[name]
        cls._bookmarks.clear()
        cls._bookmarks[name] = bookmark

    @classmethod
    def _get_special_type(cls, name: Optional[str], obj: Any) -> Optional[str]:
        """
        Return special type name of `obj` named `name` (`None` if not special).
        """
        try:
            return next(
                special_type
                for special_type in (
                    special_type_detector(name, obj)
                    for special_type_detector in cls.special_type_detectors
                )
                if special_type is not None
            )
        except StopIteration:
            if (
                isinstance(name, str)
                and len(name) > 4
                and name.startswith("__")
                and name.endswith("__")
            ):
                return "magic"
            elif (
                isinstance(name, str)
                and len(name) > 1
                and name.startswith("_")
            ):
                return "private"
            elif callable(obj) and not isinstance(obj, type):
                return "callable"
            else:
                return None

    @classmethod
    def get_handler_cache(
        cls, handler: Optional[type[DeepVarsHandler]] = None,
    ) -> DeepVarsHandler:
        """
        Return handler from cache, creating it and caching if it's not there.

        :param handler: A handler class or `None` (which is equivalent to
            `cls.default_handler`).
        :return: An instance of a `DeepVarsHandler` subclass.
        """
        if handler is None:
            handler = cls.default_handler
        try:
            result = cls._handlers_cache[handler]
        except KeyError:
            result = cls._handlers_cache[handler] = handler(cls)
        return result

    @classmethod
    def get_handler(cls, name: Optional[str], obj: Any) -> DeepVarsHandler:
        """
        Return a handler for `obj`.
        """
        special_handler = cls._get_special_type(name, obj)
        handler = None
        if special_handler is not None:
            handler = cls._handlers.get(special_handler)
        if handler is None:
            handler = cls._handlers.get(type(obj), cls.default_handler)
        return cls.get_handler_cache(cast(type[DeepVarsHandler], handler))

    @classmethod
    def use_obj(
        cls, name: Optional[str], obj: Any, deep_vars_args: dict[str, Any],
    ) -> bool:
        """
        Return `True` if `obj` is to be used in :py:meth:`deep_vars` output.
        """
        return cls.get_handler(name, obj).use_obj(obj, deep_vars_args)

    @classmethod
    def deep_vars(
        cls,
        obj: Any,
        max_depth: int = 1,
        _obj_name: Optional[str] = None,
        _top_level: bool = True,
    ) -> Any:
        """
        Return `vars`-like dictionary for `obj`.

        Note that the loops are not detected. For example:

        ```
        >>> from deep_vars import deep_vars
        >>> x = [1]
        >>> x.append(x)
        >>> x
        [1, [...]]
        >>> deep_vars(x, 0)
        [1, [...]]
        >>> deep_vars(x)
        [1, [...]]
        >>> deep_vars(x, 2)
        [1, [1, [1, [...]]]]
        ```

        :param obj: Any object (including those that do not work with `vars`).
        :param max_depth: Maximum dept to go to with sub-objects. If set to 0,
            no processing is done. If set to 1 (which is the default), the
            behaviour is the same as for `vars` (except that it works with
            objects of any type). If set to 1, attributes of `obj` will get
            processed as well. And so on.
        :return: A dictionary like the one that you'd expect to get from
            `vars(obj)`, possibly with some of the attributes also converted to
            dictionaries.
        """
        if max_depth <= 0:
            return obj
        try:
            return cls.get_handler(
                _obj_name, obj,
            ).process(
                obj, {"max_depth": max_depth - 1, "_top_level": False},
            )
        except DeepVarsInvalidHandlerError as e:
            if _top_level:
                raise NotImplementedError(str(e)) from e
            else:
                raise

    @classmethod
    def set_handlers(
        cls,
        value: type[DeepVarsHandler],
        *handlers: str | type[DeepVarsHandler],
    ) -> None:
        """
        Set handlers to the given value.
        """
        if not handlers:
            raise ValueError("at least one handler needs to be provided")
        cls._handlers.update({handler: value for handler in handlers})

    @classmethod
    def set_special_handlers(
        cls,
        value: type[DeepVarsHandler],
        *,
        skip: Optional[Iterable[str]] = None,
    ) -> None:
        """
        Set special (string-named) handlers to the given value.
        """
        skip = set() if skip is None else set(skip)
        cls.set_handlers(
            value,
            *(
                name
                for name in cls._handlers
                if isinstance(name, str) and name not in skip
            ),
        )

    @classmethod
    def set_all_handlers(cls, value: type[DeepVarsHandler]) -> None:
        """
        Set all available handlers to the given value.
        """
        cls.set_handlers(value, *cls._handlers.keys())


DEFAULT_BOOKMARK = DeepVars.bookmark_handlers()


def deep_vars(obj: Any, max_depth: int = 1) -> Any:
    DeepVars.deep_vars.__doc__
    return DeepVars.deep_vars(obj, max_depth)
