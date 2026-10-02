import os

from dotenv import load_dotenv

load_dotenv()


# --------------------------------------------------
# Agent
# --------------------------------------------------

AGENT_NAME = "Jarvis Miller"

ROOT_PATH = "/home/andreas/projects/jarvis-miller"

CHECK_INTERVAL = 1800  # 30 Minuten


# --------------------------------------------------
# GitHub
# --------------------------------------------------

REPOSITORY_NAME = "awack27/sandbox-for-jarvis"

REPOSITORY_PATH = "/home/andreas/projects/sandbox-for-jarvis"

REPOSITORY_URL = (
    "git@github-jarvis:awack27/sandbox-for-jarvis.git"
)

BOT_USERNAME = "EQjmi"

GITHUB_EMAIL = "Jarvis.Miller@gmx.de"

GITHUB_TOKEN_PATH = "/home/andreas/projects/jarvis-miller/token.txt"

# --------------------------------------------------
# SSH
# --------------------------------------------------

SSH_KEY_PATH = "/home/awa/.ssh/id_ed25519"


# --------------------------------------------------
# Ollama
# --------------------------------------------------

OLLAMA_HOST = "http://localhost:11434"

OLLAMA_MODEL = "qwen2.5-coder"


# --------------------------------------------------
# Workspace
# --------------------------------------------------

WORKSPACE_ROOT = "workspaces"

PROMPT_DIRECTORY = "prompts"

LOG_DIRECTORY = "logs"