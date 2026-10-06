from pathlib import Path

from git import Repo
from git import GitCommandError
import subprocess


class GitClient:

    def __init__(self, repository_path: str):

        self.repository_path = Path(repository_path)

        if not self.repository_path.exists():
            raise FileNotFoundError(
                f"Repository not found: {repository_path}"
            )

        self.repo = Repo(repository_path)

    def clone_repository(
        self,
        repo_url: str,
        target_path: str
    ):

        return Repo.clone_from(
            repo_url,
            target_path
        )

    def current_branch(self) -> str:

        return self.repo.active_branch.name

    def create_branch(
        self,
        branch_name: str
    ):

        self.repo.git.checkout(
            "-b",
            branch_name
        )

    def checkout(
        self,
        branch_name: str
    ):

        self.repo.git.checkout(
            branch_name
        )

    def add_all(self):

        self.repo.git.add(A=True)

    def commit(
        self,
        message: str
    ):

        if not self.repo.is_dirty(
            untracked_files=True
        ):
            return

        self.repo.index.commit(
            message
        )

    def push(
        self,
        branch_name: str = ""
    ):

        branch = (
            branch_name
            or self.current_branch()
        )

        self.repo.git.push(
            "--set-upstream",
            "origin",
            branch
        )

    def pull(self):

        self.repo.remotes.origin.pull()

    def fetch(self):

        self.repo.remotes.origin.fetch()

    def checkout_main(self):

        self.checkout("main")

    def delete_branch(
        self,
        branch_name: str
    ):

        self.repo.git.branch(
            "-D",
            branch_name
        )

    def create_branch_from_main(
        self,
        branch_name: str
    ):

        self.checkout_main()

        self.pull()

        self.create_branch(
            branch_name
        )

    def has_changes(self) -> bool:

        return self.repo.is_dirty(
            untracked_files=True
        )

    def push_current_branch(self):

        self.push(
            self.current_branch()
        )

    def commit_and_push(
        self,
        commit_message: str
    ):

        self.add_all()

        self.commit(
            commit_message
        )

        self.push_current_branch()

    def get_current_commit(self) -> str:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(self.repository_path),
                "rev-parse",
                "HEAD"
            ],
            capture_output=True,
            text=True,
            check=True
        )

        return result.stdout.strip()

    def get_changed_files(self, old_commit: str) -> list[Path]:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                old_commit,
            ],
            cwd=self.repository_path,
            capture_output=True,
            text=True,
            check=True,
        )

        return [
            Path(line)
            for line in result.stdout.splitlines()
            if line.strip()
        ]

    def commit_exists(self, commit: str) -> bool:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=self.repository_path,
            capture_output=True,
            text=True,
        )

        return result.returncode == 0