import io
import os
import re


class config:
    def __init__(self, name="", context="", typ="", description=""):
        self.name = name
        self.context = context
        self.typ = typ
        self.description = description

    def get_package(self):
        return re.match(r""".*?([^ ]*config).*""", self.context).group(1)


class configs:
    def __init__(self):
        self.confs = dict()

    def update(self, conf):
        if conf.name not in self.confs:
            self.confs[conf.name] = list()
        self.confs[conf.name].append(conf)

#cfgs = configs()


def find_py_files(dir):
    for dirpath, dirname, filenames in os.walk(dir):
        for filename in filenames:
            if os.path.splitext(filename)[1] == ".py" or \
                    os.path.splitext(filename)[1] == ".html":
                yield os.path.join(dirpath, filename)


def find_config(filename, cfgs=None):
    with io.open(filename, 'r', encoding="UTF-8") as f:
        code = f.read()
    for m in re.finditer(r"""(?x)^.*(config (?:\.get_?(.*?)\(|\[)
            '(.*?)' #matching group for name
            (?:,.*?)? (?:\)|\])).*$ # group 1 for comlete config
            """, code, re.MULTILINE):
        if cfgs is not None:
            fds = config(m.group(3), m.group(), m.group(2))
            #print(m.group(2)),
            #print(m.group(1))
            cfgs.update(fds)
        yield m.group(3)


def get_sorted_configs(dir, cfgs=None):
    s = set()
    for f in find_py_files(dir):
        s.update(find_config(f, cfgs))
    return sorted(s)


def get_defaults(filename):
    with io.open(filename, 'r', encoding="UTF-8") as f:
        code = f.read()
    defaults = re.search(r"""DEFAULTS = \{((.*?))\}""", code,
                         re.MULTILINE | re.DOTALL).group(1)
    cfgs = configs()
    for m in re.finditer(r"""^ [^u\n]*?\'(.*?)\'.*?,\n""",
                         defaults, re.MULTILINE):
        fds = config(m.group(1), m.group)
        cfgs.update(fds)
        #print(m.group(1)),
        #print(" ###")
    return cfgs


def print_cfgs(cfgs):
    for key in sorted(cfgs.confs.viewkeys()):
        print(key),
        print(": "),
        for conf in cfgs.confs[key]:
            print(conf.typ),
            None
        print("")


def print_confs():
    cfgs = configs()
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    get_sorted_configs(os.path.join(ROOT, 'src'), cfgs)
    print_cfgs(cfgs)


def print_defaults():
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfgs = get_defaults(os.path.join(ROOT, 'src/adhocracy/config/__init__.py'))
    print_cfgs(cfgs)


def print_missing():
    cfgs = configs()
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    get_sorted_configs(os.path.join(ROOT, 'src'), cfgs)
    defaults = get_defaults(os.path.join(ROOT, 'src/adhocracy/config/__init__.py'))
    for key in sorted(cfgs.confs.viewkeys()):
        miss = True
        for key2 in sorted(defaults.confs.viewkeys()):
            if key == key2:
                miss = False
        if miss:
            print(key)


def print_obsolete():
    cfgs = configs()
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    get_sorted_configs(os.path.join(ROOT, 'src'), cfgs)
    defaults = get_defaults(os.path.join(ROOT, 'src/adhocracy/config/__init__.py'))
    for key in sorted(defaults.confs.viewkeys()):
        miss = True
        for key2 in sorted(cfgs.confs.viewkeys()):
            if key == key2:
                miss = False
        if miss:
            print(key)

#get_defaults("../src/adhocracy/config/__init__.py")
#print_missing()
print_obsolete()
#print_defaults()
#print_confs()

