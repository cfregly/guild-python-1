# Plugin Python utils

The module `guild.plugins.python_util` provides tools for plugins when
working with Python scripts and modules.

    >>> from guild.plugins import python_util

## Enumerating Python scripts

Some plugins can enumerate models in a location. To assist with this,
python utils provides `scripts_for_location`.

    >>> scripts = python_util.scripts_for_location(
    ...   sample("scripts"), exclude=["*/__init__.py"])
    >>> sorted([script.name for script in scripts])
    ['mnist_mlp']

NOTE: The use of exclude is a work-around for cases when Bazel
generates a __init__.py for the sample directory on build.

Scripts can be inspected for various declarations. Let's example the
'mnist_mlp' script:

    >>> mnist_mlp = scripts[0]

The script source can be read using the `src` attribute:

    >>> mnist_mlp.src
    '.../samples/scripts/mnist_mlp.py'

A script name is the base name (without extension) of the script
source:

    >>> mnist_mlp.name
    'mnist_mlp'

We can enumerate various script declarations.

Imports:

    >>> mnist_mlp.imports()
    ['__future__',
     'keras',
     'keras.datasets',
     'keras.models',
     'keras.layers',
     'keras.optimizers']

Calls:

    >>> pprint([call.path for call in mnist_mlp.calls()])
    ['mnist.load_data',
     'x_train.reshape',
     'x_test.reshape',
     'x_train.astype',
     'x_test.astype',
     'print',
     'print',
     'keras.utils.to_categorical',
     'keras.utils.to_categorical',
     'Sequential',
     'model.add',
     'model.add',
     'model.add',
     'model.add',
     'model.add',
     'model.summary',
     'model.compile',
     'model.fit',
     'model.evaluate',
     'print',
     'print',
     'Dense',
     'Dropout',
     'Dense',
     'Dropout',
     'Dense',
     'RMSprop',
     'keras.callbacks.TensorBoard']

## Sorting script objects

Script objects returned by `python_util` can be sorted according to
their path.

    >>> [script.src for script in sorted([
    ...   python_util.Script("c"),
    ...   python_util.Script("a"),
    ...   python_util.Script("d"),
    ...   python_util.Script("b"),
    ... ])]
    ['a', 'b', 'c', 'd']

## Wrapping methods

Plugins routinely patch the environment to perform additional
actions. One such patch is to listen for method calls on various
classes. The `listen_method` function can be used to reveive
notification when a method is called.

Let's create a class with a method that prints a message:

    >>> class Hello(object):
    ...   def say(self, msg):
    ...     print(msg)

Let's patch `say`:

    >>> def wrap_say(say, msg):
    ...   say("I've wrapped '%s'" % msg)
    >>> python_util.listen_method(Hello, "say", wrap_say)

When we call `hello` on an object:

    >>> hello = Hello()
    >>> hello.say("Hello Guild!")
    I've wrapped 'Hello Guild!'
    Hello Guild!

The arg `say` is the original wrapped function, which can be called by
the wrapping function.

We can wrap a method multiple times. In this case we'll wrap using an
instance method:

    >>> class Wrapper(object):
    ...   def __init__(self, cls, method_name):
    ...     python_util.listen_method(cls, method_name, self.wrap_say)
    ...
    ...   def wrap_say(self, say, msg):
    ...     say("I've also wrapped '%s'" % msg)

    >>> wrapper = Wrapper(Hello, "say")
    >>> hello.say("Hello again!")
    I've wrapped 'Hello again!'
    I've also wrapped 'Hello again!'
    Hello again!

A wrapper can circumvent the call to the original method and return
its own value by raising `python_util.Result`:

    >>> def wrap_and_prevent(say, msg):
    ...   say("I've wrapped '%s' and prevented the original call!" % msg)
    ...   raise python_util.Result(None)
    >>> python_util.listen_method(Hello, "say", wrap_and_prevent)
    >>> hello.say("Hello once more!")
    I've wrapped 'Hello once more!'
    I've also wrapped 'Hello once more!'
    I've wrapped 'Hello once more!' and prevented the original call!

Any errors generated by a wrapper are logged and isolated. Let's
illustrate by creating a wrapper that generates an error:

    >>> def wrap_error(say, msg):
    ...    1 / 0

Let's add this function and call `say` while capturing logs:

    >>> python_util.listen_method(Hello, "say", wrap_error)

    >>> log_capture = LogCapture()
    >>> with log_capture:
    ...   hello.say("And again!")
    I've wrapped 'And again!'
    I've also wrapped 'And again!'
    I've wrapped 'And again!' and prevented the original call!

Note the other three callbacks were called successfully.

Here's what was logged during that call:

    >>> log_capture.print_all()
    ERROR: callback
    Traceback (most recent call last):
    ...
    ZeroDivisionError: ...

We can remove wrappers using `remove_method_listener`:

    >>> python_util.remove_method_listener(hello.say, wrap_and_prevent)
    >>> python_util.remove_method_listener(hello.say, wrap_error)

    >>> hello.say("Again, once more!")
    I've wrapped 'Again, once more!'
    I've also wrapped 'Again, once more!'
    Again, once more!

Finally, we can remove all listeners on a method:

    >>> python_util.remove_method_listeners(hello.say)
    >>> hello.say("Hello, without listeners!")
    Hello, without listeners!

In our final example, we'll replace a method that increments a value
with a new function.

Here's our class and method:

    >>> class Calc(object):
    ...   def incr(self, x):
    ...     return x + 1

And our class and method in action:

    >>> calc = Calc()
    >>> calc.incr(1)
    2

Here's a function that supports a second argument, which specifies the
amount to increment by. Note we return a result by raising
`python_util.Result` (as in the previous example). Note we don't use
the original method (represented by the `_incr` argument) because
we're replacing it altogether.

    >>> def incr2(_incr, x, incr_by=1):
    ...   raise python_util.Result(x + incr_by)

We wrap the original:

    >>> python_util.listen_method(Calc, "incr", incr2)

And here's our new behavior:

    >>> calc.incr(1)
    2
    >>> calc.incr(1, 2)
    3

Let's unwrap and confirm that we no longer have access to the new
function:

    >>> python_util.remove_method_listener(Calc.incr, incr2)
    >>> calc.incr(1)
    2
    >>> calc.incr(1, 2)
    Traceback (most recent call last):
    TypeError: incr() takes exactly 2 arguments (3 given)

What happens when we add two listeners that both provide results? The
behavior is as follows:

- All listeners are notified, regardless of whether any have raised
  Result exceptions

- The last raised Result is returned as the result of the method call

Here are two listeners, both of which provide results:

    >>> def incr_by_2(_incr, x):
    ...    print("incr_by_2 called")
    ...    raise python_util.Result(x + 2)

    >>> def incr_by_3(_incr, x):
    ...    print("incr_by_3 called")
    ...    raise python_util.Result(x + 3)

Let's add both as listeners:

    >>> python_util.listen_method(Calc, "incr", incr_by_2)
    >>> python_util.listen_method(Calc, "incr", incr_by_3)

And test our method:

    >>> calc.incr(1)
    incr_by_2 called
    incr_by_3 called
    4

Here we see that both listeners were called, but result is returned
from the last to provide a result.

Let re-order our listeners to confirm:

    >>> python_util.remove_method_listeners(Calc.incr)
    >>> python_util.listen_method(Calc, "incr", incr_by_3)
    >>> python_util.listen_method(Calc, "incr", incr_by_2)

    >>> calc.incr(1)
    incr_by_3 called
    incr_by_2 called
    3
