# import datetime
from github import Github
import re
import requests
from .Utils import parse_toolchain_date

def get_dependencies_from_lakefile(lakefile_str: str)-> set[str]:
    dependency_re_str = r'require\s+(.*?)\s+from\s+git\s+"(.*?)"\s+@\s+"(.*?)"'
    dependency_re = re.compile(dependency_re_str)
    dep_data = dependency_re.findall(lakefile_str)
    answer = set(map(lambda dep: dep[0], dep_data))
    # for dep in dep_data: # TODO: Figure out if this is what we want
    #     answer[dep[0]] = {
    #         "url": dep[1],
    #         "sha": dep[2]
    #     }
    return answer

class LeanProject():
    def __init__(self, name: str, owner: str) -> None:
        self.name = name
        self.owner = owner
        self.github_url = f"https://github.com/{self.owner}/{self.name}"
        self.repo = None
        self.get_dependencies()
        self.get_toolchain()
        self.get_sha()

    def get_repo(self):
        if self.repo:
            return self.repo
        else:
            g = Github()
            print(f"checking:{self.owner}/{self.name}")
            self.repo = g.get_repo(f"{self.owner}/{self.name}")
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
    
# class ExternalProject(LeanProject):
#     def __init__(self, name: str) -> None:
#         super().__init__(name)
