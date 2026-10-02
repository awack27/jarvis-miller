import logging
import time

from src.config import settings
from src.git_tools.git_client import GitClient
from src.github_api.github_client import GitHubClient
from src.llm.ollama_client import OllamaClient
from src.llm.prompt_builder import PromptBuilder
from src.history.memory_handler import MemoryHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def main():

    logging.info("Starting Jarvis Miller...")

    git_client = GitClient(
        repository_path=settings.REPOSITORY_PATH
    )
    logging.info("GitClient ready")

    github_client = GitHubClient(
        token_path=settings.GITHUB_TOKEN_PATH,
        repository_name=settings.REPOSITORY_NAME,
        bot_username=settings.BOT_USERNAME
    )
    logging.info("GithubClient ready")

    ollama_client = OllamaClient(
        model=settings.OLLAMA_MODEL
    )
    logging.info("OllamaClient ready")

    prompt_builder = PromptBuilder()

    logging.info("MemoryHandler reads repository...")
    memory_handler = MemoryHandler(settings.REPOSITORY_PATH, ollama_client=ollama_client)    
    memory_handler.get_repository().print_repo(functions=True, summaries=True)
    logging.info("MemoryHandler ready")

    while True:

        try:

            logging.info("Starting new cycle...")

            #
            # 1. Check for update in main
            #
            git_client.checkout("main")
            git_client.pull()

            #
            # 2. Check comments on open PRs
            #
            open_prs = github_client.get_open_pull_requests()
            print("Debug: ", open_prs)

            for pr in open_prs:

                comments = github_client.get_issue_comments(
                    pr
                )

                if comments:

                    logging.info(
                        f"Found review comments on PR #{pr.number}"
                    )

                    # here work on comment

                    break

            else:

                #
                # 3. Check assigned issues
                #
                assigned_issues = github_client.get_assigned_issues()

                if assigned_issues:

                    issue = min(assigned_issues, key=lambda x: x.number)

                    logging.info(f"Working on issue #{issue.number}")


                    # work on ticket

                else:

                    logging.info(
                        "No open work found."
                    )

        except Exception as e:

            logging.exception(
                "Unexpected error occurred:"
            )

            logging.exception(e)

        logging.info(
            f"Sleeping for {settings.CHECK_INTERVAL} seconds..."
        )

        time.sleep(settings.CHECK_INTERVAL)


if __name__ == "__main__":
    main()