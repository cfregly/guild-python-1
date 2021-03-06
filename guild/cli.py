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

import functools

import click

TABLE_COL_SPACING = 2

try:
    input = raw_input
except NameError:
    input = input

def error(msg=None, exit_status=1):
    raise SystemExit(msg, exit_status)

def out(s="", **kw):
    click.echo(s, **kw)

def table(data, cols, sort=None, detail=None, indent=0, err=False):
    data = sorted(data, key=_table_row_sort_key(sort))
    formatted = _format_data(data, cols + (detail or []))
    col_info = _col_info(formatted, cols)
    for item in formatted:
        _item_out(item, cols, col_info, detail, indent, err)

def _table_row_sort_key(sort):
    if not sort:
        return lambda _: 0
    else:
        return functools.cmp_to_key(lambda x, y: _item_cmp(x, y, sort))

def _item_cmp(x, y, sort):
    if isinstance(sort, str):
        return _val_cmp(x, y, sort)
    else:
        for part in sort:
            part_cmp = _val_cmp(x, y, part)
            if part_cmp != 0:
                return part_cmp
        return 0

def _val_cmp(x, y, sort):
    if sort.startswith("-"):
        sort = sort[1:]
        rev = -1
    else:
        rev = 1
    x_val = x.get(sort)
    y_val = y.get(sort)
    return rev * ((x_val > y_val) - (x_val < y_val))

def _format_data(data, cols):
    formatted = []
    for item0 in data:
        item = {}
        formatted.append(item)
        for col in cols:
            item[col] = str(item0.get(col, ""))
    return formatted

def _col_info(data, cols):
    info = {}
    for item in data:
        for col in cols:
            coli = info.setdefault(col, {})
            coli["width"] = max(coli.get("width", 0), len(item[col]))
    return info

def _item_out(item, cols, col_info, detail, indent, err):
    indent_padding = " " * indent
    click.echo(indent_padding, nl=False, err=err)
    for i, col in enumerate(cols):
        val = item[col]
        last_col = i == len(cols) - 1
        padded = _pad_col_val(val, col, col_info) if not last_col else val
        click.echo(padded, nl=False, err=err)
    click.echo(err=err)
    for key in (detail or []):
        click.echo(indent_padding, nl=False, err=err)
        click.echo("  %s: %s" % (key, item[key]), err=err)

def _pad_col_val(val, col, col_info):
    return val.ljust(col_info[col]["width"] + TABLE_COL_SPACING)

def confirm(prompt, default=False):
    click.echo(prompt, nl=False)
    click.echo(" %s " % ("(Y/n)" if default else "(y/N)"), nl=False)
    c = input()
    yes_vals = ["y", "yes"]
    if default:
        yes_vals.append("")
    return c.lower().strip() in yes_vals
