import json
from pathlib import Path

from .repository import Repository
from src.llm.ollama_client import OllamaClient
from src.git_tools.git_client import GitClient
from src.config import settings

class RepositoryCache:
    CACHE_VERSION = 1

    def __init__(self, repository_path: Path | str):
        self.repository_path = Path(repository_path).resolve()

        self.cache_directory = (
            Path(settings.ROOT_PATH) / ".cache" / "jarvis"
        )

        self.cache_file = (
            self.cache_directory / "repository.json"
        )
        self.git_client = GitClient(repository_path)

    def exists(self) -> bool:
        return self.cache_file.exists()

    def save(
        self,
        repository: Repository,
    ):
        self.cache_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        self.last_commit = self.git_client.get_current_commit()

        data = {
            "cache_version": self.CACHE_VERSION,
            "repository_path": str(
                repository.repository_path
            ),
            "last_commit": self.last_commit,
            "repository": repository.to_dict(),
        }

        self.cache_file.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

    def load(
        self,
        ollama_client: OllamaClient | None = None
    ) -> Repository:
        if not self.exists():
            raise FileNotFoundError(
                f"Repository cache does not exist: "
                f"{self.cache_file}"
            )

        data = json.loads(
            self.cache_file.read_text(
                encoding="utf-8"
            )
        )

        if data["cache_version"] != self.CACHE_VERSION:
            raise ValueError(
                "Repository cache version is not supported."
            )

        return Repository.from_dict(
            data["repository"],
            ollama_client=ollama_client
        )

    def get_last_commit(self) -> str | None:
        if not self.exists():
            return None

        data = json.loads(
            self.cache_file.read_text(
                encoding="utf-8"
            )
        )

        return data.get("last_commit")

    def is_up_to_date(self) -> bool:
        if not self.exists():
            return False

        cached_commit = self.get_last_commit()

        current_commit = (
            self.git_client.get_current_commit()
        )

        return cached_commit == current_commit

    def load_if_valid(
        self,
        ollama_client: OllamaClient | None = None
    ) -> Repository | None:

        if not self.exists():
            return None

        if not self.is_up_to_date():
            return None

        return self.load(
            ollama_client=ollama_client
        )