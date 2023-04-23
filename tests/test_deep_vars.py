from copy import copy, deepcopy
from typing import Any, Optional

from deep_vars import (
    deep_vars, DeepVars, DeepVarsHandler, DeepVarsHandlerCallable,
    DeepVarsHandlerHide,
)

from .utils import TestsBase


class DataObjectBase:
    def __init__(self, **kwargs: Any) -> None:
        self._keys = tuple(kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)


class DataObject(DataObjectBase):
    public_class_var = 1719
    _private_class_var = 1923


class DataObjectCallableTest(DataObject):
    some_lambda = lambda cls, x: 2 * x  # noqa: E731
    not_callable = 17.19

    def some_callable(self, y: int) -> str:
        return str(y)


class DataObjectWithError:

    def __init__(self):
        self.a = 17

    def __dir__(self):
        return ["a", "non_existing_attribute"]


class DeepVarsHandlerSpecial(DeepVarsHandler):

    def process(self, obj: Any, deep_vars_args: dict[str, Any]) -> Any:
        return {
            "fields": self.deep_vars.deep_vars(obj._keys, **deep_vars_args),
        }


def _special_detector(name: Optional[str], obj: Any) -> Optional[str]:
    return (
        "specially_detected"
        if getattr(obj, "specially_detected", False) else
        None
    )


class DeepVarsHandlerTest(DeepVarsHandler):

    def process(self, obj: Any, deep_vars_args: dict[str, Any]) -> Any:
        return str(obj)


class TestDeepVars(TestsBase):

    def test_simple(self):
        data = DataObject(
            a=17,
            b="foo",
            c=DataObject(a=19, b="bar", c=DataObject(a=23)),
        )

        result = deep_vars(data)

        self.assertEqual(
            result,
            {"public_class_var": 1719, "a": 17, "b": "foo", "c": data.c},
        )
        self.assertTrue(result["c"] is data.c)

        self.assertTrue(deep_vars(data, 0) is data)

        result = deep_vars(data, 1)

        self.assertEqual(
            result,
            {"public_class_var": 1719, "a": 17, "b": "foo", "c": data.c},
        )
        self.assertTrue(result["c"] is data.c)

        result = deep_vars(data, 2)

        self.assertEqual(
            result,
            {
                "public_class_var": 1719,
                "a": 17,
                "b": "foo",
                "c": {
                    "public_class_var": 1719,
                    "a": 19,
                    "b": "bar",
                    "c": data.c.c,
                },
            },
        )
        self.assertTrue(result["c"]["c"] is data.c.c)

        result = deep_vars(data, 3)
        expected = {
            "public_class_var": 1719,
            "a": 17,
            "b": "foo",
            "c": {
                "public_class_var": 1719,
                "a": 19,
                "b": "bar",
                "c": {"public_class_var": 1719, "a": 23},
            },
        }

        self.assertEqual(result, expected)

        # Should be the same as the previous one.
        result = deep_vars(data, 4)

        self.assertEqual(result, expected)

    def test_error(self):
        data = DataObjectWithError()
        self.assertEqual(
            deep_vars(data),
            {"a": 17, "non_existing_attribute": DeepVars.error_object},
        )
        self.assertEqual(str(DeepVars.error_object), "<<<ERROR>>>")
        self.assertEqual(repr(DeepVars.error_object), "<<<ERROR>>>")

    def test_list(self):
        data = DataObjectBase(some_list=["foo", "bar", DataObjectBase(x=17)])

        self.assertEqual(
            deep_vars(data, 1), {"some_list": data.some_list},
        )
        self.assertEqual(
            deep_vars(data, 2), {"some_list": data.some_list},
        )
        self.assertEqual(
            deep_vars(data, 3),
            {"some_list": data.some_list[:2] + [{"x": 17}]},
        )

    def test_tuple(self):
        data = DataObjectBase(some_tuple=("foo", "bar", DataObjectBase(x=17)))

        self.assertEqual(
            deep_vars(data, 1), {"some_tuple": data.some_tuple},
        )
        self.assertEqual(
            deep_vars(data, 2), {"some_tuple": data.some_tuple},
        )
        self.assertEqual(
            deep_vars(data, 3),
            {"some_tuple": data.some_tuple[:2] + ({"x": 17},)},
        )

    def test_set(self):
        data = DataObjectBase(some_set={"foo", "bar", DataObjectBase(x=17)})

        self.assertEqual(
            deep_vars(data, 1), {"some_set": data.some_set},
        )
        self.assertEqual(
            deep_vars(data, 2), {"some_set": data.some_set},
        )
        self.assertEqual(
            # dict would not fit in a set, so we don't process
            # `DataObjectBase(x=17)`.
            deep_vars(data, 3), {"some_set": data.some_set},
        )

    def test_dict(self):
        data = DataObjectBase(
            some_dict={"foo": 1, "bar": DataObjectBase(x=17)},
        )

        self.assertEqual(
            deep_vars(data, 1), {"some_dict": data.some_dict},
        )
        self.assertEqual(
            deep_vars(data, 2), {"some_dict": data.some_dict},
        )
        self.assertEqual(
            deep_vars(data, 3), {"some_dict": {"foo": 1, "bar": {"x": 17}}},
        )

    def test_set_all_handlers(self):
        DeepVars.set_all_handlers(DeepVarsHandlerTest)
        for key, value in DeepVars._handlers.items():
            self.assertEqual(
                value, DeepVarsHandlerTest, f"handler type {repr(key)}",
            )

    def test_callable(self):
        DeepVars.set_all_handlers(DeepVarsHandlerHide)
        DeepVars.set_handlers(DeepVarsHandlerCallable, "callable", float)
        self.assertEqual(
            deep_vars(DataObjectCallableTest(foo="bar"), 8),
            {
                "some_lambda": "<lambda>(x)",
                "some_callable": "some_callable(y: int) -> str",
                "not_callable": DeepVars.error_object,
            },
        )

    def test_set_special_handlers(self):
        DeepVars.set_all_handlers(DeepVarsHandlerHide)
        DeepVars.set_special_handlers(
            DeepVarsHandlerTest, skip=["callable"],
        )
        for key, value in DeepVars._handlers.items():
            expected = (
                DeepVarsHandlerTest
                if isinstance(key, str) and key != "callable" else
                DeepVarsHandlerHide
            )
            self.assertEqual(value, expected, f"handler type: {repr(key)}")

    def test_bookmarks_add_remove(self):
        cnt = len(DeepVars._bookmarks)
        first_key = next(iter(DeepVars._bookmarks))
        first = DeepVars._bookmarks[first_key]

        DeepVars.bookmark_handlers("test_bookmarks_name_1")
        DeepVars.bookmark_handlers()
        DeepVars.bookmark_handlers("test_bookmarks_name_2")
        DeepVars.bookmark_handlers()
        DeepVars.bookmark_handlers()
        DeepVars.bookmark_handlers()
        DeepVars.bookmark_handlers()
        DeepVars.bookmark_handlers()
        self.assertEqual(len(DeepVars._bookmarks), cnt + 8)

        DeepVars.reset_handlers()
        self.assertEqual(len(DeepVars._bookmarks), cnt + 7)

        DeepVars.reset_handlers(delete=True)
        self.assertEqual(len(DeepVars._bookmarks), cnt + 6)

        DeepVars.reset_handlers(delete=False)
        self.assertEqual(len(DeepVars._bookmarks), cnt + 6)

        DeepVars.reset_handlers("test_bookmarks_name_1")
        self.assertEqual(len(DeepVars._bookmarks), cnt + 6)

        DeepVars.reset_handlers("test_bookmarks_name_1", delete=True)
        self.assertEqual(len(DeepVars._bookmarks), cnt + 5)

        with self.assertRaises(KeyError):
            DeepVars.reset_handlers("test_bookmarks_name_1")

        with self.assertRaises(KeyError):
            DeepVars.reset_handlers("test_bookmarks_name_1", delete=True)

        with self.assertRaises(KeyError):
            DeepVars.reset_handlers("test_bookmarks_name_1", delete=False)

        DeepVars.reset_handlers("test_bookmarks_name_2", delete=False)
        self.assertEqual(len(DeepVars._bookmarks), cnt + 5)

        self.assertTrue("test_bookmarks_name_1" not in DeepVars._bookmarks)
        self.assertTrue("test_bookmarks_name_2" in DeepVars._bookmarks)

        DeepVars.clear_bookmarks()
        self.assertEqual(len(DeepVars._bookmarks), 1)
        first_key_2 = next(iter(DeepVars._bookmarks))
        self.assertEqual(first_key, first_key_2)
        self.assertTrue(DeepVars._bookmarks[first_key] is first)

    def test_reset_empty(self):
        DeepVars.reset_handlers()
        self.assertEqual(len(DeepVars._bookmarks), 1)
        expected = deepcopy(DeepVars._bookmarks)

        DeepVars.reset_handlers()
        self.assertEqual(len(DeepVars._bookmarks), 1)
        self.assertEqual(DeepVars._bookmarks, expected)

    def test_nameless(self):
        cnt = len(DeepVars._bookmarks)
        expected_handlers = copy(DeepVars._handlers)
        expected_handlers_cache = copy(DeepVars._handlers_cache)

        DeepVars.bookmark_handlers()
        DeepVars.set_handlers(DeepVarsHandlerTest, DataObject)
        DeepVars._handlers_cache[DataObject] = DeepVarsHandlerTest
        DeepVars.reset_handlers()

        self.assertEqual(DeepVars._handlers, expected_handlers)
        self.assertEqual(DeepVars._handlers_cache, expected_handlers_cache)
        self.assertEqual(len(DeepVars._bookmarks), cnt)

    def test_nameled_alone(self):
        cnt = len(DeepVars._bookmarks)
        expected_handlers = copy(DeepVars._handlers)
        expected_handlers_cache = copy(DeepVars._handlers_cache)

        DeepVars.bookmark_handlers("name")
        DeepVars.set_handlers(DeepVarsHandlerTest, DataObject)
        DeepVars._handlers_cache[DataObject] = DeepVarsHandlerTest
        DeepVars.reset_handlers("name")

        self.assertEqual(DeepVars._handlers, expected_handlers)
        self.assertEqual(DeepVars._handlers_cache, expected_handlers_cache)
        self.assertEqual(len(DeepVars._bookmarks), cnt + 1)

        DeepVars.reset_handlers()
        self.assertEqual(len(DeepVars._bookmarks), cnt)

    def test_named_plus_one(self):
        cnt = len(DeepVars._bookmarks)
        expected_handlers = copy(DeepVars._handlers)

        DeepVars.bookmark_handlers("name")
        DeepVars.set_handlers(DeepVarsHandlerTest, DataObject)
        DeepVars._handlers_cache[DataObject] = DeepVarsHandlerTest
        DeepVars.bookmark_handlers()
        DeepVars.reset_handlers("name")

        self.assertEqual(DeepVars._handlers, expected_handlers)
        self.assertEqual(len(DeepVars._bookmarks), cnt + 2)

        DeepVars.reset_handlers()
        self.assertEqual(len(DeepVars._bookmarks), cnt + 1)
        DeepVars.reset_handlers()
        self.assertEqual(len(DeepVars._bookmarks), cnt)

    def test_special_detectors(self):
        data = DataObject(foo=17, specially_detected=True)

        self.assertEqual(
            deep_vars(data),
            {"foo": 17, "public_class_var": 1719, "specially_detected": True},
        )

        DeepVars.special_type_detectors.append(_special_detector)
        DeepVars.set_handlers(DeepVarsHandlerSpecial, "specially_detected")
        try:
            self.assertEqual(
                deep_vars(data), {"fields": ("foo", "specially_detected")},
            )
        finally:
            DeepVars.special_type_detectors.pop()

    def test_base_handler(self):
        DeepVars.set_handlers(DeepVarsHandler, int)
        with self.assertRaises(NotImplementedError):
            deep_vars(DataObjectBase(x=17), 2)

    def test_handler_hide_default_fallback(self):
        DeepVars.set_handlers(DeepVarsHandlerHide, int)
        self.assertEqual(deep_vars(17), 17)

    def test_handler_hide_custom_fallback(self):
        DeepVars.set_handlers(DeepVarsHandlerHide, int)
        DeepVarsHandlerHide.fallback_handler = DeepVarsHandlerTest
        try:
            self.assertEqual(deep_vars(17), "17")
        finally:
            DeepVarsHandlerHide.fallback_handler = None

    def test_empty_set_handlers(self):
        with self.assertRaises(ValueError):
            DeepVars.set_handlers(DeepVarsHandler)

    def test_get_default_handler(self):
        self.assertTrue(
            isinstance(DeepVars.get_handler_cache(), DeepVars.default_handler),
        )

    def test_failed_process(self):
        class BrokenDir:
            def __dir__(self):
                raise NotImplementedError("whoopsie!")

        obj = BrokenDir()
        self.assertTrue(deep_vars(obj) is obj)

    def test_callable_with_missing_signature(self):
        self.assertEqual(deep_vars(dir), "<built-in function>")
