import io
import os
import re


class config:
    def __init__(self, name="", context="", typ=""):
        self.name = name
        self.context = context
        self.typ = typ

    def get_package(self):
        return re.match(r""".*?([^ ]*config).*""", self.context).group(1)


class configs:
    def __init__(self):
        self.confs = dict()

    def update(self, conf):
        if conf.name not in self.confs:
            self.confs[conf.name] = list()
        self.confs[conf.name].append(conf)

cfgs = configs()


def find_py_files(dir):
    for dirpath, dirname, filenames in os.walk(dir):
        for filename in filenames:
            if os.path.splitext(filename)[1] == ".py" or \
                    os.path.splitext(filename)[1] == ".html":
                yield os.path.join(dirpath, filename)


def find_config(filename):
    with io.open(filename, 'r', encoding="UTF-8") as f:
        code = f.read()
    for m in re.finditer(r"""(?x)^.*(config (?:\.get_?(.*?)\(|\[)
            '(.*?)' #matching group for name
            (?:,.*?)? (?:\)|\])).*$ # group 1 for comlete config
            """, code, re.MULTILINE):
        fds = config(m.group(3), m.group(), m.group(2))
        print(m.group(2)),
        print(m.group(1))
        cfgs.update(fds)
        yield m.group(3)


def get_sorted_configs(dir):
    s = set()
    for f in find_py_files(dir):
        s.update(find_config(f))
    return sorted(s)


get_sorted_configs("../src")
for key in cfgs.confs.viewkeys():
    #print(key),
    #print(": "),
    for conf in cfgs.confs[key]:
        #print(conf.typ),
        None
    #print("")

ROOT = os.path.dirname(os.path.normpath(__file__))
configs = get_sorted_configs(os.path.join(ROOT, 'src'))
print('\n'.join(configs))

