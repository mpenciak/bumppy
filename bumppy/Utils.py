import re
from datetime import datetime

def parse_toolchain_date(toolchain_string: str):
    toolchain_re = re.compile(r"[\d]{4}-[\d]{2}-[\d]{2}")
    toolchain_match = toolchain_re.search(toolchain_string)
    if toolchain_match:
        toolchain_date = datetime.strptime(toolchain_match.group(), "%Y-%m-%d")
    else:
        raise Exception("Unable to parse toolchain string")
    return toolchain_date