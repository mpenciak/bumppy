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
