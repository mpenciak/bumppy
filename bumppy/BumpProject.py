from github import Github
from datetime import datetime
import re

def parse_toolchain_date(toolchain_string: str):
    toolchain_re = re.compile(r"[\d]{4}-[\d]{2}-[\d]{2}")
    toolchain_match = toolchain_re.search(toolchain_string)
    if toolchain_match:
        toolchain_date = datetime.strptime(toolchain_match.group(), "%Y-%m-%d")
    else:
        raise Exception("Unable to parse toolchain string")
    return toolchain_date

class BumpProject():
    def __init__(self, org: str, target_date: datetime, roots) -> None:
        self.org = org
        self.target_date = target_date
        if not self.verify_lean_toolchain():
            raise Exception("Lean toolchain not supported")
        self.roots = roots

    def verify_lean_toolchain(self):
        g = Github()
        release_repo = g.get_repo("leanprover/lean4-nightly")
        tags = release_repo.get_tags()
        tag_names = map(lambda x: x.name, tags)
        tag_dates = map(lambda name: parse_toolchain_date(name), tag_names)
        if self.target_date in tag_dates:
            return True
        else:
            return False

    @classmethod
    def from_toml(cls, bump_data):
        org = bump_data["org"]
        date = bump_data["date"]
        root_repos = bump_data["repos"]
        return cls(org, date, root_repos)
