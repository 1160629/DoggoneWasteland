from glob import glob
from os import chdir


def get_dir_modules(d):
    # get python modules in a given directory
    chdir(d)
    modules = list(f.split(".")[0] for f in glob("*.py"))
    return modules

def file_lines(fpath):
    with open(fpath, "r") as f:
        contents = f.readlines()

    return len(contents)

def search_modules(l):
    lines = 0
    for m in l:
        fpath = m + ".py"
        lines += file_lines(fpath)

    return lines

def search_folder(folder):
    modules = get_dir_modules(folder)
    lines = search_modules(modules)
    print(lines)

if __name__ == "__main__":
    search_folder(".")