import tomli
import os
from pathlib import Path
import re
from .BumpProject import BumpProject
import pickle

# TODO: This module should contain the CLI

CURR_DIR = Path(os.curdir)

def get_bump_project():
    with open(CURR_DIR/"bump.toml", 'rb') as file:
        bump_data = tomli.load(file)
    return BumpProject.from_toml(bump_data)

def from_restart(file_path: str) -> BumpProject:
    with open(file_path, 'rb') as file:
        return pickle.load(file)

def dump_self(project: BumpProject):
    with open('./bumpproject', 'wb') as file:
        pickle.dump(project, file)