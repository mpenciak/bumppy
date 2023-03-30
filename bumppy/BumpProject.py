from github import Github
from datetime import datetime
import networkx as nx
import requests
from .LeanProject import LeanProject
from .Utils import parse_toolchain_date

class BumpProject():
    def __init__(self, owner: str, target_date: datetime, root_names: list[str]) -> None:
        self.owner = owner
        self.target_date = target_date
        # if not self.verify_lean_toolchain(): # TODO: Fix this
        #     raise Exception("Lean toolchain not supported")
        
        self.get_std_commit()

        self.root_names = root_names
        self.repo_dict: dict[str, LeanProject] = {}

        for name in self.root_names: 
            self.repo_dict[name] = LeanProject(name, self.owner)

        self.dep_graph = nx.DiGraph()
        self.get_all_repos()

        self.bump_order = nx.lexicographical_topological_sort(self.dep_graph)

    # def verify_lean_toolchain(self): #TODO: This hits the rate limit
    #     g = Github()
    #     release_repo = g.get_repo("leanprover/lean4-nightly")
    #     tags = release_repo.get_tags()
    #     tag_names = list(map(lambda x: x.name, tags))
    #     tag_dates = map(lambda name: parse_toolchain_date(name), tag_names)
    #     if self.target_date in tag_dates:
    #         return True
    #     else:
    #         return False
    
    def get_std_commit(self): #TODO: Do something better for external repos in general
        g = Github()
        std_repo = g.get_repo("leanprover/std4")
        commits = std_repo.get_commits()
        for commit in commits:
            ref = commit.raw_data["sha"]
            file = std_repo.get_contents("lean-toolchain",ref)
            std_toolchain = parse_toolchain_date(requests.get(file.download_url).text) #pyright: ignore
            if std_toolchain <= self.target_date:
                break
            else:
                pass
        self.std_sha = commit.commit.raw_data['sha'] #pyright: ignore

    @classmethod
    def from_toml(cls, bump_data):
        owner = bump_data["owner"]
        date = bump_data["date"]
        root_repos = bump_data["root_repos"]
        return cls(owner, date, root_repos)

    @classmethod
    def from_restart(cls):
        pass

    def add_repo_deps(self, repo_name: str):
        repo = self.repo_dict[repo_name]
        for dep in repo.deps:
            if dep != 'std4' and not dep in self.repo_dict: # TODO: Do something better for external repos in general
                self.repo_dict[dep] = LeanProject(dep, self.owner)
                self.dep_graph.add_edge(dep, repo_name)
                self.add_repo_deps(dep)
            else:
                pass

    def get_all_repos(self):
        for repo_name in self.root_names:
            self.add_repo_deps(repo_name)
            