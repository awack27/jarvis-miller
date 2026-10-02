from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from src.llm.ollama_client import OllamaClient



SUPPORTED_EXTENSIONS = {
    ".py",
}


IGNORED_DIRECTORIES = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "site-packages",
}


@dataclass
class Function:
    function_header: str
    function_body: str
    function_summary: str | None = None

    def to_dict(self) -> dict:
        return {
            "function_header": self.function_header,
            "function_body": self.function_body,
            "function_summary": self.function_summary,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Function":
        return cls(
            function_header=data["function_header"],
            function_body=data["function_body"],
            function_summary=data.get("function_summary"),
        )

    def create_summary(self, ollama_client: OllamaClient):
        prompt = f"""
        Summarize the following Python function in a maximum of 15 words. 
        Describe only what the function does. No introduction. No Markdown formatting. 
        Function: {self.function_body}
        """ 
        self.function_summary = ollama_client.generate(prompt) 
        return self.function_summary


@dataclass
class Class:
    class_name: str
    class_methods: list[Function] = field(default_factory=list)
    class_summary: str | None = None

    def to_dict(self) -> dict:
        return {
            "class_name": self.class_name,
            "class_methods": [
                method.to_dict()
                for method in self.class_methods
            ],
            "class_summary": self.class_summary,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Class":
        return cls(
            class_name=data["class_name"],
            class_methods=[
                Function.from_dict(method)
                for method in data.get("class_methods", [])
            ],
            class_summary=data.get("class_summary"),
        )

    def create_summary(self, ollama_client: OllamaClient):
        methods = "\n".join(
            f"- {method.function_header}: {method.function_summary}"
            for method in self.class_methods
            if method.function_summary
        )

        prompt = f"""
Summarize the following Python class in a maximum of 20 words.

Briefly describe the responsibility of the class.
No introduction.
No Markdown formatting.

Class name:
{self.class_name}

Methods:
{methods}
"""

        self.class_summary = ollama_client.generate(prompt)

        return self.class_summary


@dataclass
class File:
    file_path: Path
    file_imports: str = ""
    file_classes: list[Class] = field(default_factory=list)
    functions: list[Function] = field(default_factory=list)
    file_summary: str | None = None

    def __post_init__(self):
        if self.file_path.suffix == ".py":
            self._parse_python()

    def to_dict(self) -> dict:
        return {
            "file_path": str(self.file_path),
            "file_imports": self.file_imports,
            "file_classes": [
                class_.to_dict()
                for class_ in self.file_classes
            ],
            "functions": [
                function.to_dict()
                for function in self.functions
            ],
            "file_summary": self.file_summary,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "File":
        file = cls.__new__(cls)

        file.file_path = Path(data["file_path"])
        file.file_imports = data.get("file_imports", "")
        file.file_classes = [
            Class.from_dict(class_)
            for class_ in data.get("file_classes", [])
        ]
        file.functions = [
            Function.from_dict(function)
            for function in data.get("functions", [])
        ]
        file.file_summary = data.get("file_summary")

        return file


    def _parse_python(self):
        try:
            source = self.file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(self.file_path))
        except (OSError, UnicodeDecodeError, SyntaxError):
            return

        self.file_imports = self._extract_imports(tree)

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.functions.append(
                    self._create_function(node, source)
                )

            elif isinstance(node, ast.ClassDef):
                self.file_classes.append(
                    self._create_class(node, source)
                )

    def _extract_imports(self, tree: ast.Module) -> str:
        imports = []

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.unparse(node))

        return "\n".join(imports)

    def _create_class(
        self,
        node: ast.ClassDef,
        source: str
    ) -> Class:
        class_methods = []

        for child in node.body:
            if isinstance(
                child,
                (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                class_methods.append(
                    self._create_function(child, source)
                )

        return Class(
            class_name=node.name,
            class_methods=class_methods
        )

    def _create_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        source: str
    ) -> Function:
        lines = source.splitlines()

        start = node.lineno - 1
        end = node.end_lineno

        function_body = "\n".join(lines[start:end])

        return Function(
            function_header=lines[start],
            function_body=function_body
        )
    
    def create_summary(self, ollama_client: OllamaClient):
        classes = "\n".join(
            f"- {class_.class_name}: {class_.class_summary}"
            for class_ in self.file_classes
            if class_.class_summary
        )

        functions = "\n".join(
            f"- {function.function_header}: "
            f"{function.function_summary}"
            for function in self.functions
            if function.function_summary
        )

        prompt = f"""
Summarize the following Python file in a maximum of 30 words.

Describe the main purpose of the file and its most important responsibilities.
No introduction.
No Markdown formatting.

File name:
{self.file_path.name}

Imports:
{self.file_imports}

Classes:
{classes}

Functions:
{functions}
"""

        self.file_summary = ollama_client.generate(prompt)

        return self.file_summary


@dataclass
class Folder:
    folder_path: Path
    files: list[File] = field(default_factory=list)
    folders: list[Folder] = field(default_factory=list)
    folder_summary: str | None = None

    def __post_init__(self):
        self._parse()

    def to_dict(self) -> dict:
        return {
            "folder_path": str(self.folder_path),
            "files": [
                file.to_dict()
                for file in self.files
            ],
            "folders": [
                folder.to_dict()
                for folder in self.folders
            ],
            "folder_summary": self.folder_summary,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Folder":
        folder = cls.__new__(cls)

        folder.folder_path = Path(data["folder_path"])
        folder.files = [
            File.from_dict(file)
            for file in data.get("files", [])
        ]
        folder.folders = [
            Folder.from_dict(child_folder)
            for child_folder in data.get("folders", [])
        ]
        folder.folder_summary = data.get("folder_summary")

        return folder

    def _parse(self):
        if not self.folder_path.exists():
            return

        for path in sorted(self.folder_path.iterdir()):
            if path.is_dir():
                if path.name in IGNORED_DIRECTORIES:
                    continue

                if path.name.startswith("."):
                    continue

                self.folders.append(
                    Folder(path)
                )

            elif path.is_file():
                if path.suffix not in SUPPORTED_EXTENSIONS:
                    continue

                self.files.append(
                    File(path)
                )
    
    def create_summary(self, ollama_client: OllamaClient):
        files = "\n".join(
            f"- {file.file_path.name}: {file.file_summary}"
            for file in self.files
            if file.file_summary
        )

        folders = "\n".join(
            f"- {folder.folder_path.name}/: "
            f"{folder.folder_summary}"
            for folder in self.folders
            if folder.folder_summary
        )

        prompt = f"""
Summarize the following project folder in a maximum of 30 words.

Describe its main responsibility and what kind of code it contains.
No introduction.
No Markdown formatting.

Folder:
{self.folder_path.name}

Files:
{files}

Subfolders:
{folders}
"""

        self.folder_summary = ollama_client.generate(prompt)

        return self.folder_summary

class Repository:
    def __init__(self, repository_path: Path | str, ollama_client: OllamaClient):
        self.repository_path = Path(repository_path).resolve()
        self.ollama_client = ollama_client

        self.files: list[File] = []
        self.folders: list[Folder] = []

        self.repository_summary: str | None = None

        self._parse()

    def to_dict(self) -> dict:
        return {
            "repository_path": str(self.repository_path),
            "files": [
                file.to_dict()
                for file in self.files
            ],
            "folders": [
                folder.to_dict()
                for folder in self.folders
            ],
            "repository_summary": self.repository_summary,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
        ollama_client: OllamaClient | None = None
    ) -> "Repository":
        repository = cls.__new__(cls)

        repository.repository_path = Path(
            data["repository_path"]
        )
        repository.files = [
            File.from_dict(file)
            for file in data.get("files", [])
        ]
        repository.folders = [
            Folder.from_dict(folder)
            for folder in data.get("folders", [])
        ]
        repository.repository_summary = data.get(
            "repository_summary"
        )
        repository.ollama_client = ollama_client

        return repository

    def _parse(self):
        if not self.repository_path.exists():
            raise FileNotFoundError(
                f"Repository does not exist: {self.repository_path}"
            )

        if not self.repository_path.is_dir():
            raise NotADirectoryError(
                f"Repository path is not a directory: "
                f"{self.repository_path}"
            )

        for path in sorted(self.repository_path.iterdir()):
            if path.is_dir():
                if path.name in IGNORED_DIRECTORIES:
                    continue

                if path.name.startswith("."):
                    continue

                self.folders.append(Folder(path))

            elif path.is_file():
                if path.suffix not in SUPPORTED_EXTENSIONS:
                    continue

                self.files.append(File(path))

    def print_repo(
        self,
        functions: bool = False,
        summaries: bool = False
    ):
        print(self.repository_path.name)

        # Files directly in the repository
        for file in self.files:
            self._print_file(
                file=file,
                prefix="├── ",
                functions=functions,
                summaries=summaries
            )

        # Folders in the repository
        for index, folder in enumerate(self.folders):
            is_last = index == len(self.folders) - 1

            self._print_folder(
                folder=folder,
                prefix="",
                is_last=is_last,
                functions=functions,
                summaries=summaries
            )


    def _print_folder(
        self,
        folder: Folder,
        prefix: str,
        is_last: bool,
        functions: bool,
        summaries: bool
    ):
        connector = "└── " if is_last else "├── "

        print(
            f"{prefix}{connector}{folder.folder_path.name}/"
        )

        if summaries and folder.folder_summary:
            print(
                f"{prefix}    Summary: {folder.folder_summary}"
            )

        child_prefix = prefix + (
            "    " if is_last else "│   "
        )

        # Files
        for index, file in enumerate(folder.files):
            is_last_file = (
                index == len(folder.files) - 1
                and len(folder.folders) == 0
            )

            self._print_file(
                file=file,
                prefix=child_prefix,
                connector="└── " if is_last_file else "├── ",
                functions=functions,
                summaries=summaries
            )

        # Subfolders
        for index, child_folder in enumerate(folder.folders):
            is_last_folder = (
                index == len(folder.folders) - 1
            )

            self._print_folder(
                folder=child_folder,
                prefix=child_prefix,
                is_last=is_last_folder,
                functions=functions,
                summaries=summaries
            )


    def _print_file(
        self,
        file: File,
        prefix: str,
        functions: bool,
        summaries: bool,
        connector: str = "├── "
    ):
        print(
            f"{prefix}{connector}{file.file_path.name}"
        )

        if summaries and file.file_summary:
            print(
                f"{prefix}    Summary: {file.file_summary}"
            )

        if not functions:
            return

        function_prefix = prefix + "    "

        # Top-level functions
        for function in file.functions:
            print(
                f"{function_prefix}├── "
                f"{function.function_header}"
            )

            if summaries and function.function_summary:
                print(
                    f"{function_prefix}    "
                    f"Summary: {function.function_summary}"
                )

        # Classes and their methods
        for class_index, class_ in enumerate(file.file_classes):
            is_last_class = (
                class_index == len(file.file_classes) - 1
            )

            class_connector = (
                "└── " if is_last_class else "├── "
            )

            print(
                f"{function_prefix}{class_connector}"
                f"class {class_.class_name}"
            )

            if summaries and class_.class_summary:
                print(
                    f"{function_prefix}    "
                    f"Summary: {class_.class_summary}"
                )

            method_prefix = function_prefix + "    "

            for method_index, method in enumerate(
                class_.class_methods
            ):
                method_connector = (
                    "└── "
                    if method_index == len(class_.class_methods) - 1
                    else "├── "
                )

                print(
                    f"{method_prefix}{method_connector}"
                    f"{method.function_header}"
                )

                if summaries and method.function_summary:
                    print(
                        f"{method_prefix}    "
                        f"Summary: {method.function_summary}"
                    )
    
    def create_summary(self):
        if self.ollama_client is None:
            raise RuntimeError(
                "OllamaClient is required to create summaries."
            )

        # --------------------------------------------------------------
        # 1. Functions
        # --------------------------------------------------------------

        for file in self.files:
            for function in file.functions:
                function.create_summary(self.ollama_client)

            for class_ in file.file_classes:
                for method in class_.class_methods:
                    method.create_summary(self.ollama_client)

        # --------------------------------------------------------------
        # 2. Classes
        # --------------------------------------------------------------

        for file in self.files:
            for class_ in file.file_classes:
                class_.create_summary(self.ollama_client)

        # --------------------------------------------------------------
        # 3. Files
        # --------------------------------------------------------------

        for file in self.files:
            file.create_summary(self.ollama_client)

        # --------------------------------------------------------------
        # 4. Folders
        # --------------------------------------------------------------

        for folder in self.folders:
            self._create_folder_summaries(folder)

        # --------------------------------------------------------------
        # 5. Repository
        # --------------------------------------------------------------

        self._create_repository_summary()


    def _create_folder_summaries(self, folder: Folder):
        for child_folder in folder.folders:
            self._create_folder_summaries(child_folder)

        for file in folder.files:
            # The files were already summarized above.
            pass

        folder.create_summary(self.ollama_client)

    def _create_repository_summary(self):
        files = "\n".join(
            f"- {file.file_path.name}: {file.file_summary}"
            for file in self.files
            if file.file_summary
        )

        folders = "\n".join(
            self._build_folder_summary(folder)
            for folder in self.folders
        )

        prompt = f"""
Summarize the following software repository in a maximum of 50 words.

Briefly describe the purpose of the project and its most important components.
No introduction.
No Markdown formatting.

Repository:
{self.repository_path.name}

Files:
{files}

Folders:
{folders}
"""

        self.repository_summary = (
            self.ollama_client.generate(prompt)
        )

    def _build_folder_summary(self, folder: Folder) -> str:
        result = (
            f"- {folder.folder_path.name}/: "
            f"{folder.folder_summary}"
        )

        for child in folder.folders:
            result += "\n" + self._build_folder_summary(child)

        return result
