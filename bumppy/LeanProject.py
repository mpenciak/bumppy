# import datetime
from github import Github
from git.repo import Repo
from pathlib import Path
import os
from datetime import date
import re
import requests
import subprocess
from .Utils import parse_toolchain_date
from .secret import TOKEN

def get_dependencies_from_lakefile(lakefile_str: str):
    dependency_re_str = r'require\s+(.*?)\s+from\s+git\s+"(.*?)"\s+@\s+"(.*?)"'
    dependency_re = re.compile(dependency_re_str)
    dep_data = dependency_re.findall(lakefile_str)
    answer:dict[str,dict[str, str]] = dict()
    for dep in dep_data: 
        answer[dep[0]] = {
            "url": dep[1],
            "sha": dep[2]
        }
    return answer

class LeanProject():
    def __init__(self, url_name: str, owner: str) -> None:
        self.url_name = url_name
        self.owner = owner
        self.github_url = f"https://github.com/{self.owner}/{self.url_name}"
        self.repo = None
        self.get_dependencies()
        self.get_toolchain()
        self.get_sha()

    def get_repo(self):
        if self.repo:
            return self.repo
        else:
            g = Github(login_or_token=TOKEN)
            print(f"checking:{self.owner}/{self.url_name}")
            self.repo = g.get_repo(f"{self.owner}/{self.url_name}")
            return self.repo

    def get_dependencies(self):
        repo = self.get_repo()
        content_file = repo.get_contents('lakefile.lean')
        file_content = requests.get(content_file.download_url) #pyright: ignore
        lakefile_text = file_content.text
        deps = get_dependencies_from_lakefile(lakefile_text)
        self.deps = deps

    def get_toolchain(self):
        repo = self.get_repo()
        content_file = repo.get_contents('lean-toolchain')
        lean_toolchain_text = requests.get(content_file.download_url).text #pyright: ignore
        self.main_toolchain = parse_toolchain_date(lean_toolchain_text)

    def get_sha(self):
        repo = self.get_repo()
        main_branch = repo.default_branch
        self.main_sha = repo.get_branch(main_branch).commit.sha

    def clone(self):
        curr_dir = Path(os.curdir)
        self.local_path = curr_dir / self.url_name
        Repo.clone_from(self.github_url, self.local_path)
    
    def checkout_bump_commit(self,target_date: date):
        local_repo = Repo(self.local_path)
        pp_date = target_date.strftime("%Y-%m-%d")
        branch_name = f"bump-to-{pp_date}"
        new_branch = local_repo.create_head(branch_name)
        new_branch.checkout()
    
    def bump_toolchain(self, target_date: date):
        local_repo = Repo(self.local_path)
        pp_date = target_date.strftime("%Y-%m-%d")
        toolchain_str = f"leanprover/lean4:nightly-{pp_date}"
        toolchain_path = self.local_path / "lean-toolchain"
        with open(toolchain_path, 'w') as file:
            file.write(toolchain_str)
        local_repo.index.add(['lean-toolchain'])
        new_commit = local_repo.index.commit('bump toolchain file')
        return new_commit.binsha.hex()

    def bump_dep_shas(self, sha_dict: dict[str, str]):
        local_repo = Repo(self.local_path)
        lakefile_path = self.local_path / "lakefile.lean"
        with open(lakefile_path, 'r') as read_file:
            lakefile_str = read_file.read()
        
        new_lakefile_str = lakefile_str
        for dep in self.deps:
            new_lakefile_str = new_lakefile_str.replace(self.deps[dep]['sha'], sha_dict[dep])

        with open(lakefile_path, 'w') as write_file:
            write_file.write(new_lakefile_str)
        
        local_repo.index.add(['lakefile.lean'])
        new_commit = local_repo.index.commit('bump dependencies in lakefile')
        return new_commit.binsha.hex()

    def attempt_build(self):
        process = subprocess.run(["lake", "build"], cwd=self.local_path)
        if not process.returncode == 0:
            print("Building failed, please check this repo")
        
    def attempt_test(self):
        process = subprocess.run(["lake", "exe", "lspec"], cwd=self.local_path)
        if not process.returncode == 0:
            print("Some tests failed, please check this repo")

    def push_changes(self):
        local_repo = Repo(self.local_path)
        origin = local_repo.remotes[0]
        local_repo.git.push("--set-upstream", origin, local_repo.head.ref)