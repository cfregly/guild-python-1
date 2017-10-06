# Plugin Python utils

The module `guild.plugins.python_util` provides tools for plugins when
working with Python scripts and modules.

    >>> from guild.plugins import python_util

## Enumerating Python scripts

Some plugins can enumerate models in a location. To assist with this,
python utils provides `scripts_for_location`.

    >>> scripts = python_util.scripts_for_location(sample("scripts"))
    >>> sorted([script.name for script in scripts])
    ['__init__', 'mnist_mlp']

NOTE: The script '__init__' is generated by Bazel during a build and
is not part of the list of sample scripts.

Scripts can be inspected for various declarations. Let's example the
'mnist_mlp' script:

    >>> mnist_mlp = scripts[1]

The script source can be read using the `src` attribute:

    >>> mnist_mlp.src
    '.../samples/scripts/mnist_mlp.py'

A script name is the base name (without extension) of the script
source:

    >>> mnist_mlp.name
    'mnist_mlp'

We can enumerate various script declarations.

Imports:

    >>> script.imports()
    ['__future__',
     'keras',
     'keras.datasets',
     'keras.models',
     'keras.layers',
     'keras.optimizers']

Calls:

    >>> pprint([call.path for call in script.calls()])
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
    >>> python_util.listen_method(Hello.say, wrap_say)

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
    ...   def __init__(self, method):
    ...     python_util.listen_method(method, self.wrap_say)
    ...
    ...   def wrap_say(self, say, msg):
    ...     say("I've also wrapped '%s'" % msg)

    >>> wrapper = Wrapper(Hello.say)
    >>> hello.say("Hello again!")
    I've wrapped 'Hello again!'
    I've also wrapped 'Hello again!'
    Hello again!

A wrapper can prevent the call to the wrapped function by returning
False.

    >>> def wrap_and_prevent(say, msg):
    ...   say("I've wrapped '%s' and prevented the original call!" % msg)
    ...   return False
    >>> python_util.listen_method(Hello.say, wrap_and_prevent)
    >>> hello.say("Hello once more!")
    I've wrapped 'Hello once more!'
    I've also wrapped 'Hello once more!'
    I've wrapped 'Hello once more!' and prevented the original call!

Any errors generated by a wrapper are logged and isolated. Let's
illustrate by creating a wrapper that generates an error:

    >>> def wrap_error(say, msg):
    ...    1 / 0

Let's add this function and call `say` while capturing logs:

    >>> python_util.listen_method(Hello.say, wrap_error)

    >>> log_capture = LogCapture()
    >>> with log_capture:
    ...   hello.say("And again!")
    I've wrapped 'And again!'
    I've also wrapped 'And again!'
    I've wrapped 'And again!' and prevented the original call!

Note the other three callbacks were called successfully.

Here's what was logged during that call:

    >>> log_capture.print_all()
    callback error
    Traceback (most recent call last):
    ...
    ZeroDivisionError: integer division or modulo by zero

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