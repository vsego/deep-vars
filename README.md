# `deep_vars`

A package providing `deep_vars` function that serves a purpose similar to `vars`, but it works with any object and can recursively process attributes as well.

## Content

1. [Basic use](#basic-use)
2. [Configuration](#configuration)
    1. [Handlers](#handlers)
    2. [Further configuration specific to some handlers](#further-configuration-specific-to-some-handlers)
    3. [Extending handlers](#extending-handlers)

## Basic use

This is used in a way similar to `vars`. For example, the following code:

```python
from dataclasses import dataclass
from typing import Optional

from deep_vars import deep_vars


@dataclass
class Foo:
    x: int
    y: Optional["Foo"] = None


foo = Foo(17, y=Foo(19))
print("vars:                     ", vars(foo))
print("deep_vars:                ", deep_vars(foo))
print("deep_vars with maxdepth=2:", deep_vars(foo, 2))
```

will print this:

```
vars:                      {'x': 17, 'y': Foo(x=19, y=None)}
deep_vars:                 {'x': 17, 'y': Foo(x=19, y=None)}
deep_vars with maxdepth=2: {'x': 17, 'y': {'x': 19, 'y': None}}
```

Note that, because it covers objects of all classes, `deep_vars` might not product a dictionary. For example, if we define `foo` in the above code like this:

```python
foo = [Foo(17), "foo", 17]
```

the `vars` print would just raise an exception:

```
TypeError: vars() argument must have __dict__ attribute`
```

while the `deep_var` outputs will be:

```
deep_vars:                 [Foo(x=17, y=None), 'foo', 17]
deep_vars with maxdepth=2: [{'x': 17, 'y': None}, 'foo', 17]
```

## Configuration

`deep_vars` is meant to be simple to use, like `vars`, so its only arguments are the object being represented and the maximum depth down to witch the conversion should go.

However, there are various possibilities for configuring it for the whole project. This is done through the attributes of `DeepVars` class.

### Handlers

The main thing one can adjust is how various objects are handled. This is done by assigning "handler types". For example, this will cause all `float` and `str` attributes to remain hidden:

```python
DeepVars.set_handlers(DeepVarsHandlerHide, float, str)
```

There are several `DeepVarsHandler<something>` classes that can be used:

* `DeepVarsHandler`: Default class, used as a parent class for all the others. It should not be used directly.
* `DeepVarsHandlerShow`: Show the object as it is (i.e., don't process it).
* `DeepVarsHandlerHide`: Skip the attribute from the output. Note that this does not affect the top level call of `deep_vars`.
* `DeepVarsHandlerProcess`: Process it in the previously described manner (similar to `vars`).
* `DeepVarsHandlerLoop`: Loop the object (usually a list or a tuple) and process each item individually.
* `DeepVarsHandlerLoopDict`: Loop the object as a dictionary, using its `items` method (can be changed in inherited classes) and process each `(key, value)` pair individually.
* `DeepVarsHandlerCallable`: Special handler for callables, converting them to signature strings.

One can also configure the default handler for those attributes that are not individually set. For example, to have them show without any processing:

```python
DeepVars.default_handler = DeepVarsHandlerShow
```

Let us take another look at the above example:

```python
DeepVars.set_handlers(DeepVarsHandlerHide, float, str)
```

The first argument is a handler class. The rest of them describe the objects that this class is used for. These are usually types, but they can also be strings. The following are recognised:

* `"magic"`: A magic attribute. These are usually methods with names starting and ending in double underscores (for example, `__init__`), but `deep_vars` will consider any attribute, even non-callable ones, for the sake of output's consistency.

* `"private"`: Any object that has a name starting with an underscore (for example, `_private` or `__very_private`).

* `"callable"`: Any callable object (a function, a method, a `lambda`) except classes.

The handlers assignment is done in the same way as it is for type-based kinda of arguments:

```python
# Hide all "callable" arguments (not including classes):
DeepVars.set_handlers(DeepVarsHandlerHide, "callable")
# Hide all `float` and all "callable" arguments (not including classes):
DeepVars.set_handlers(DeepVarsHandlerHide, float, "callable")
```

### Further configuration specific to some handlers

Some of the handlers can be fine-tuned.

`DeepVarsHandlerLoopDict` normally uses object's `items()` method to go through its items. However, this can be replaced by changing `DeepVarsHandlerLoopDict.items_method_name` to something other than `"items"`. Further, if this other method requires arguments, these can be set up as a tuple `DeepVarsHandlerLoopDict.items_method_args` and a dictionary `DeepVarsHandlerLoopDict.items_method_kwargs`.

All container handlers (`DeepVarsHandlerLoopDict`, `DeepVarsHandlerLoop`, and `DeepVarsHandlerProcess`) and also have the filtering of their items turned on or off. If turned off (`class_name.allow_filtering = False`), their items will show even if their handler is set to `DeepVarsHandlerHide`. This is the default for (`DeepVarsHandlerLoopDict` and `DeepVarsHandlerLoop`. If the filtering is turned on (`class_name.allow_filtering = True`), their items will be hidden if their handler decides so (i.e., if it is set to `DeepVarsHandlerHide`). This is the default for `DeepVarsHandlerProcess`.

### Extending handlers

One can easily define their own special object types. Here is an example from the tests:

```python
def special_detector(name: Optional[str], obj: Any) -> Optional[str]:
    return (
        "specially_detected"
        if getattr(obj, "specially_detected", False) else
        None
    )


DeepVars.special_type_detectors.append(special_detector)
DeepVars.set_handlers(DeepVarsHandlerSpecial, "specially_detected")
```

First, we need to define a callable (usually a function) that detects the special type of the argument. This callable takes attribute's name (either a string or `None`, the latter being used for the top level call of `deep_vars`) and the object itself, returning either a string used as the name for that kind of object or `None` if the object was not identified.

Second, we add this callable to the list `DeepVars.special_type_detectors`. The three predefined special types of arguments listed above are built-in, but `special_type_detectors` is checked before they are used, so its callables can override them.

Lastly, one needs to define how is this special is handled, which is done as shown above with "callable" arguments.

This allows one to extend the functionality of `deep_vars`. Arguably, this is not very useful in regular projects, but it can be used by other packages to offer `deep_vars` functionality extended to their own needs.
