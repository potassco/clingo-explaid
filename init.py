#!/usr/bin/env python3
"""
Init script to rename project.
"""

import os
import re


def read(prompt, regex):
    """
    Read a string from command line.

    The string has to match the given regular expression.
    """
    while True:
        ret = input(prompt)
        match = re.match(regex, ret)
        if match is not None:
            return ret
        print(f"the project name has to match the regular expression: {regex}")


def main():
    """
    Rename the project.
    """
    project = read("project name: ", r"^[a-z][a-z0-9_]*$")
    author = read("author: ", r".+")
    email = read("email: ", r".+")

    replacements = {
        "fillname": project,
        "<author-email>": email,
        "<author>": author,
    }

    def replace(filepath):
        with open(filepath, "r", encoding="utf-8") as hnd:
            content = hnd.read()
            for key, val in replacements.items():
                content = content.replace(key, val)
        with open(filepath, "w", encoding="utf-8") as hnd:
            hnd.write(content)

    for rootpath in [os.path.join("src", "fillname"), "tests"]:
        for dirpath, _, filenames in os.walk(rootpath):
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                filepath = os.path.join(dirpath, filename)
                replace(filepath)

    for filepath in [
        "setup.cfg",
        "noxfile.py",
        "README.md",
        "doc/index.rst",
        ".pre-commit-config.yaml",
        ".coveragerc",
    ]:
        replace(filepath)

    os.rename(os.path.join("src", "fillname"), os.path.join("src", project))


if __name__ == "__main__":
    main()
