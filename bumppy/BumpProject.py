from github import Github
from datetime import date
import networkx as nx
import requests
import pickle
from .LeanProject import LeanProject
from .Utils import parse_toolchain_date, get_name_owner_from_url
from .secret import TOKEN
from enum import Enum

class BumpStatus(Enum):
    INIT = 0
    CLONED = 1
    CHECKEDOUT = 2
    TOOLCHAINBUMPED = 3
    DEPSHASBUMPED = 4
    BUILDS = 5
    TESTSPASS = 6

class BumpProject():
    def __init__(self, owner: str, target_date: date, root_names: list[str]) -> None:
        self.owner = owner
        self.target_date = target_date
        # if not self.verify_lean_toolchain(): # TODO: This hits the API rate limit during testing
        #     raise Exception("Lean toolchain not supported")
        
        self.get_std_target()

        self.root_names = root_names
        self.repo_dict: dict[str, LeanProject] = {}

        for name in self.root_names: 
            self.repo_dict[name] = LeanProject(name, self.owner)

        self.dep_graph = nx.DiGraph()
        self.get_all_repos()

        self.bump_order = list(nx.algorithms.dag.lexicographical_topological_sort(self.dep_graph))

        self.bump_status: dict[str, BumpStatus] = {}
        self.bump_shas: dict[str, str] = {}

    # def verify_lean_toolchain(self): #TODO: This hits the API rate limit during testing
    #     g = Github()
    #     release_repo = g.get_repo("leanprover/lean4-nightly")
    #     tags = release_repo.get_tags()
    #     tag_names = list(map(lambda x: x.name, tags))
    #     tag_dates = map(lambda name: parse_toolchain_date(name), tag_names)
    #     if self.target_date in tag_dates:
    #         return True
    #     else:
    #         return False
    
    def get_std_target(self): #TODO: Do something better for external repos in general
        g = Github(login_or_token=TOKEN)
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
        self.target_std_sha: str = commit.commit.raw_data['sha'] #pyright: ignore

    @classmethod
    def from_toml(cls, bump_data):
        owner = bump_data["owner"]
        date = bump_data["date"]
        root_repos = bump_data["root_repos"]
        return cls(owner, date, root_repos)

    @classmethod
    def from_restart(cls, file_path: str) -> "BumpProject":
        with open(file_path, 'rb') as file:
            return pickle.load(file)

    def add_repo_deps(self, repo_name: str):
        repo = self.repo_dict[repo_name]
        for dep in repo.deps:
            owner, name= get_name_owner_from_url(repo.deps[dep]["url"])
            if name != 'std4' and not name in self.repo_dict: # TODO: Do something better for external repos in general
                self.repo_dict[dep] = LeanProject(name, owner)
                self.dep_graph.add_edge(dep, repo_name)
                self.add_repo_deps(dep)
            else:
                pass

    def get_all_repos(self):
        for repo_name in self.root_names:
            self.add_repo_deps(repo_name)
    
    def dump_self(self):
        with open('./bumpproject', 'wb') as file:
            pickle.dump(self, file)
        
    def bump_leanproject(self, lpname: str): # TODO: Add logic to break and re-initiate on failed builds and tests
        lp = self.repo_dict[lpname]
        self.bump_status[lpname] = BumpStatus.INIT
        lp.clone()
        self.bump_status[lpname] = BumpStatus.CLONED
        lp.checkout_bump_commit(self.target_date)
        self.bump_status[lpname] = BumpStatus.CHECKEDOUT
        lp.bump_toolchain(self.target_date)
        self.bump_status[lpname] = BumpStatus.TOOLCHAINBUMPED
        new_sha = lp.bump_dep_shas(self.bump_shas)
        self.bump_shas[lpname] = new_sha
        self.bump_status[lpname] = BumpStatus.DEPSHASBUMPED

        lp.attempt_build()
        self.bump_status[lpname] = BumpStatus.BUILDS

        lp.attempt_test()
        self.bump_status[lpname] = BumpStatus.TESTSPASS

        lp.push_changes()

    def bump_all_projects(self):
        for project in self.bump_order:
            self.bump_leanproject(project)