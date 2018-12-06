from glob import glob
from os import chdir
import re


def get_dir_modules(d):
    # get python modules in a given directory
    chdir(d)
    modules = list(f.split(".")[0] for f in glob("*.py"))
    return modules


def get_lines(found, text):
    return list(text[:i].count("\n") for i in found)


def re_find(search_string, text):
    return [m.start() for m in re.finditer(search_string, text)]


def py_find(search_string, text):
    text_excerpt = text
    found = []
    i = -1
    total = 0
    while True:
        text_excerpt = text_excerpt[i + 1:]
        i = text_excerpt.find(search_string)
        if i == -1:
            break
        total += i
        found.append(total)
    return found


def find(search_string, text):
    # print occurences of search_string line by line
    found = py_find(search_string, text)
    lines = get_lines(found, text)
    for l in lines:
        print("\tFound " + search_string + " at line " + str(l + 1))


def find_in_file(search_string, fpath):
    with open(fpath, "r") as f:
        contents = f.read()

    find(search_string, contents)


def search_modules(search_string, l):
    for m in l:
        fpath = m + ".py"
        print("in " + fpath + "...")
        find_in_file(search_string, fpath)


def search_folder(search_for, folder):
    modules = get_dir_modules(folder)
    search_modules(search_for, modules)


if __name__ == "__main__":
    search_folder("32, 13", ".")
