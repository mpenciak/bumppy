import tomli
import os
from BumpProject import BumpProject
from pathlib import Path
import re

# TODO: This module should contain the CLI

CURR_DIR = Path(os.curdir)

def get_bump_project():
    with open(CURR_DIR/"bump.toml", 'rb') as file:
        bump_data = tomli.load(file)
    return BumpProject.from_toml(bump_data)

def get_dependencies_from_lakefile(lakefile_str: str):
    dependency_re_str = r'require\s+(.*?)\s+from\s+git\s+"(.*?)"\s+@\s+"(.*?)"'
    dependency_re = re.compile(dependency_re_str)
    dep_data = dependency_re.findall(lakefile_str)
    answer = {}
    for dep in dep_data:
        answer[dep[0]] = {
            "url": dep[1],
            "sha": dep[2]
        }
    return answer

