import io
import os
import re
import argparse


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


def print_cfgs(cfgs, cfgs2=configs()):
    for key in sorted(cfgs.confs.viewkeys()):
        if key not in cfgs2.confs.viewkeys():
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


used = configs()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
get_sorted_configs(SRC, used)
defaults = get_defaults(os.path.join(SRC, 'adhocracy/config/__init__.py'))

#print_cfgs(defaults, cfgs)

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("-u", "--used", action="store_true",
                   help="print used options in code")
group.add_argument("-d", "--default", action="store_true",
                   help="print default options in __init__.py")
parser.add_argument("-D", "--difference", action="store_true",
                    help="print the difference between used and "
                    "default options")

args = parser.parse_args()

if args.used:
    if args.difference:
        print_cfgs(used, defaults)
    else:
        print_cfgs(used)
if args.default:
    if args.difference:
        print_cfgs(defaults, used)
    else:
        print_cfgs(defaults)

#get_defaults("../src/adhocracy/config/__init__.py")
#print_missing()
#print_obsolete()
#print_defaults()
#print_confs()

