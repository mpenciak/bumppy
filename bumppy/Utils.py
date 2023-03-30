import re
from datetime import date
from urllib.parse import urlparse

def parse_toolchain_date(toolchain_string: str):
    toolchain_re = re.compile(r"[\d]{4}-[\d]{2}-[\d]{2}")
    toolchain_match = toolchain_re.search(toolchain_string)
    if toolchain_match:
        date_str = toolchain_match.group()
        year = int(date_str[0:4])
        month = int(date_str[5:7])
        day = int(date_str[8:10])
        toolchain_date = date(year, month, day)
    else:
        raise Exception("Unable to parse toolchain string")
    return toolchain_date

def get_name_owner_from_url(url: str):
    split_path = urlparse(url).path.split('/')
    owner = split_path[1]
    repo = split_path[2]
    return owner, repo
