import io
import os
import re


def find_py_files(dir):
    for dirpath, dirname, filenames in os.walk(dir):
        for filename in filenames:
            if os.path.splitext(filename)[1] == ".py":
                yield os.path.join(dirpath, filename)


def find_config(filename):
    with io.open(filename, 'r', encoding="UTF-8") as f:
        code = f.read()
    for m in re.finditer(r"""(?x)config (?:\.get\(|\[)
            '(.*?)' #matching group
            (?:,.*?)? (?:\)|\])
            """, code):
        yield m.group(1)


def get_sorted_configs(dir):
    s = set()
    for f in find_py_files(dir):
        s.update(find_config(f))
    return sorted(s)


for cfg in get_sorted_configs("../src"):
    print(cfg)
