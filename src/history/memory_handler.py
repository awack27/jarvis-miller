from pathlib import Path

from .conversation import Conversation, Chat
from .repository import Repository
from .repository_cache import RepositoryCache
from src.llm.ollama_client import OllamaClient
from src.git_tools.git_client import GitClient


class MemoryHandler:
    def __init__(
        self,
        repository_path: str | Path,
        ollama_client: OllamaClient
    ):
        self.conversation = Conversation()

        self.repository_path = Path(repository_path)
        self.ollama_client = ollama_client

        self.repository_cache = RepositoryCache(
            repository_path=self.repository_path
        )

        self.git_client = GitClient(repository_path)

        self.repository = self._load_repository()

    # ------------------------------------------------------------------
    # Conversation
    # ------------------------------------------------------------------

    def create_chat(self, ticket_nr: int) -> Chat:
        return self.conversation.create_chat(ticket_nr)

    def get_chat(self, ticket_nr: int) -> Chat | None:
        for chat in self.conversation.chats:
            if chat.ticket_nr == ticket_nr:
                return chat

        return None

    # ------------------------------------------------------------------
    # Repository
    # ------------------------------------------------------------------

    def _load_repository(self) -> Repository:
        if self.repository_cache.exists():
            if self.repository_cache.is_up_to_date():
                print("Repo up to date - load cache")
                return self.repository_cache.load_if_valid(
                    ollama_client=self.ollama_client
                )
            else:
                print("Repo is outdated")
                last_commit = self.repository_cache.get_last_commit()
                if self.git_client.commit_exists(last_commit):
                    print("Repo is outdated - load before update")
                    repository = self.repository_cache.load(self.ollama_client)
                    print("Repo is outdated - now update")
                    repository.update(last_commit, self.ollama_client)
                    self.repository_cache.save(repository)
                    return repository
                else:
                    print("Repo is outdate - commit does not exist -> new cache")

        repository = Repository(
            repository_path=self.repository_path,
            ollama_client=self.ollama_client
        )

        repository.create_summary()

        self.repository_cache.save(
            repository=repository
        )

        return repository

    def get_repository(self) -> Repository:
        return self.repository