# safe_io.py
import os
import yaml
import fnmatch
from typing import List, Optional

class SafeIO:
    """
    A sandboxed I/O handler that confines file operations to a specific
    project directory, while allowing read-only access to the agent's
    own configuration and documentation.
    """
    def __init__(self, project_dir: str, protected_config_path: str = 'protected.yaml'):
        self.agent_root = os.path.abspath('.')
        self.project_root = os.path.abspath(project_dir)
        self.protected_patterns = self._load_protected_patterns(
            os.path.join(self.agent_root, protected_config_path)
        )

        if not os.path.isdir(self.project_root):
            raise FileNotFoundError(
                f"The specified project directory does not exist: {self.project_root}"
            )

    def _load_protected_patterns(self, config_path: str) -> List[str]:
        """Loads file patterns from the agent's protected.yaml."""
        if not os.path.exists(config_path):
            print(f"Warning: Protected config '{config_path}' not found. No files will be protected.")
            return []
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _is_path_safe_for_write(self, filepath: str) -> bool:
        """Checks if a given file path is safe to write to."""
        abs_path = os.path.abspath(os.path.join(self.project_root, filepath))

        # 1. Ensure the path is within the designated project directory.
        if not abs_path.startswith(self.project_root):
            print(f"Error: Attempted to write to file '{abs_path}' outside of project directory '{self.project_root}'.")
            return False

        # 2. Check if the file matches any of the protected patterns.
        # This protects against writing to files like '.git' inside the target project.
        for pattern in self.protected_patterns:
            if fnmatch.fnmatch(os.path.basename(filepath), pattern):
                print(f"Error: Attempted to write to protected file '{filepath}' within the project directory.")
                return False

        return True

    def read(self, filepath: str) -> str:
        """
        Reads a file's content. It prioritizes reading from the project
        directory, but falls back to the agent's directory for special
        files like 'goals.md' or files in 'docs/'.
        """
        project_path = os.path.join(self.project_root, filepath)
        agent_path = os.path.join(self.agent_root, filepath)

        # Prioritize reading from the target project directory.
        if os.path.exists(project_path):
            with open(project_path, 'r', encoding='utf-8') as f:
                return f.read()

        # Fallback to the agent's directory for files that might be there.
        if os.path.exists(agent_path):
            with open(agent_path, 'r', encoding='utf-8') as f:
                return f.read()

        raise FileNotFoundError(f"File not found in project or agent directory: {filepath}")

    def write(self, filepath: str, content: str):
        """
        Writes content to a file within the project directory after
        performing safety checks.
        """
        if self._is_path_safe_for_write(filepath):
            try:
                full_path = os.path.join(self.project_root, filepath)
                directory = os.path.dirname(full_path)
                if directory:
                    os.makedirs(directory, exist_ok=True)

                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Successfully wrote to '{full_path}'.")
            except Exception as e:
                print(f"Error writing to file '{filepath}': {e}")
                raise
        else:
            raise PermissionError(f"Write access denied for file: {filepath}")