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
import re
import sys

import click

def print_info():
    _print_tensorflow_info()
    _print_tensorboard_info()

def _print_tensorflow_info():
    try:
        import tensorflow as tf
    except ImportError as e:
        err = _warn("NOT INSTALLED (%s)" % e)
        click.echo("tensorflow_version:        %s" % err)
        sys.exit(1)
    else:
        click.echo("tensorflow_version:        %s" % _tf_version(tf))
        click.echo("tensorflow_cuda_support:   %s" % _cuda_support(tf))
        click.echo("tensorflow_gpu_available:  %s" % _gpu_available(tf))
        _print_cuda_info()

def _tf_version(tf):
    return tf.__version__

def _cuda_support(tf):
    return "yes" if tf.test.is_built_with_cuda() else "no"

def _gpu_available(tf):
    return "yes" if tf.test.is_gpu_available() else "no"

def _print_cuda_info():
    proc_maps = "/proc/%s/maps" % os.getpid()
    if not os.path.exists(proc_maps):
        return
    raw = open(proc_maps, "r").read()
    version_patterns = [
        ("libcuda", "libcuda\\.so\\.([\\S]+)"),
        ("libcudnn", "libcudnn\\.so\\.([\\S]+)"),
    ]
    for name, pattern in version_patterns:
        m = re.search(pattern, raw)
        space = " " * (18 - len(name))
        if m:
            click.echo("%s_version:%s%s" % (name, space, m.group(1)))
        else:
            click.echo("%s_version:%snot loaded" % (name, space))

def _print_tensorboard_info():
    try:
        import tensorboard.version as version
    except ImportError as e:
        click.echo("tensorboard_version:       %s" % _warn("NOT INSTALLED (%s)" % e))
    else:
        click.echo("tensorboard_version:       %s" % version.VERSION)

def _warn(msg):
    return click.style(msg, fg="red", bold=True)

if __name__ == "__main__":
    print_info()
