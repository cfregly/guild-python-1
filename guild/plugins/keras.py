# Copyright 2017 TensorHub, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division

import os
from guild import plugin_util
from guild import plugin
from guild.plugins import python_util

class KerasPlugin(plugin.Plugin):

    def models_for_location(self, path):
        return python_util.script_models(
            path, _is_keras_script, _script_model)

    def enabled_for_op(self, op):
        if op.cmd != "@keras:train":
            return False, "operation not supported by plugin"
        return True, ""

    def run_op(self, op_spec, args):
        if op_spec == "train":
            _train(args)
        else:
            raise plugin.NotSupported(op_spec)

def _is_keras_script(script):
    return _imports_keras(script) and _calls_fit_method(script)

def _imports_keras(script):
    return any(
        (name == "keras" or name.startswith("keras.")
         for name in script.imports()))

def _calls_fit_method(script):
    return any((call.name == "fit" for call in script.calls()))

def _script_model(script):
    return {
        "name": script.name,
        "operations": {
            "train": {
                "cmd": "@keras:train '%s'" % os.path.abspath(script.src),
                "description": "Train the model",
            }
        }
    }

def _train(args0):
    # pylint: disable=import-error,unused-variable
    try:
        import keras
    except ImportError:
        plugin_util.exit("error: could not import keras - is it installed?")
    args = _parse_args(args0)
    _patch_keras(args)
    _exec_script(args)

def _parse_args(args0):
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("script")
    p.add_argument("--epochs", type=int)
    p.add_argument("--batch-size", type=int)
    args, _ = p.parse_known_args(args0)
    return args

def _patch_keras(args):
    # pylint: disable=import-error
    import keras
    python_util.listen_method(
        keras.models.Sequential, "fit",
        _fit_wrapper(args.batch_size, args.epochs))
    python_util.listen_method(
        keras.callbacks.TensorBoard, "set_params",
        _on_set_tensorboard_params)

def _fit_wrapper(batch_size, epochs):
    def fit(fit0, *args, **kw):
        _maybe_apply_kw("batch_size", batch_size, kw)
        _maybe_apply_kw("epochs", epochs, kw)
        _ensure_tensorboard_callback(kw)
        raise python_util.Result(fit0(*args, **kw))
    return fit

def _maybe_apply_kw(name, val, kw):
    if val:
        kw[name] = val

def _ensure_tensorboard_callback(kw):
    # pylint: disable=import-error
    import keras
    callbacks = kw.setdefault("callbacks", [])
    for cb in callbacks:
        if isinstance(cb, keras.callbacks.TensorBoard):
            break
    else:
        cb = keras.callbacks.TensorBoard(write_graph=True)
        callbacks.append(cb)
    cb.log_dir = plugin_util.current_run().path

def _find_tensorboard_cb(callbacks_list):
    # pylint: disable=import-error
    import keras
    for cb in callbacks_list:
        if isinstance(cb, keras.callbacks.TensorBoard):
            return cb
    return None

def _on_set_tensorboard_params(_set_params, params):
    run = plugin_util.current_run()
    flags = {
        name: val
        for name, val in params.items()
        if isinstance(val, (str, int, float, bool))
    }
    run.write_attr("flags", flags)

def _exec_script(args):
    python_util.exec_script(args.script)
