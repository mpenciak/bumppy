from github import Github
from datetime import datetime
import re
import LeanProject
from Utils import parse_toolchain_date


class BumpProject():
    def __init__(self, owner: str, target_date: datetime, roots) -> None:
        self.owner = owner
        self.target_date = target_date
        if not self.verify_lean_toolchain():
            raise Exception("Lean toolchain not supported")
        self.roots = roots
        self.all_repos = self.roots

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
        owner = bump_data["owner"]
        date = bump_data["date"]
        root_repos = bump_data["root_repos"]
        return cls(owner, date, root_repos)

    def get_all_repos(self):
        pass