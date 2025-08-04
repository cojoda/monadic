import os
import yaml
import fnmatch
from typing import List

class SafeIO:
    """
    A sandboxed I/O handler that prevents the agent from writing to protected
    files or accessing paths outside the project's root directory.
    """
    def __init__(self, protected_config_path: str = 'protected.yaml'):
        self.root_dir = os.path.abspath('.')
        self.protected_patterns = self._load_protected_patterns(protected_config_path)

    def _load_protected_patterns(self, config_path: str) -> List[str]:
        """Loads file patterns from the protected.yaml configuration."""
        if not os.path.exists(config_path):
            print(f"Warning: Protected config '{config_path}' not found. No files will be protected.")
            return []
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _is_path_safe(self, filepath: str) -> bool:
        """Checks if a given file path is within the project directory and not protected."""
        # 1. Prevent directory traversal attacks by resolving the absolute path.
        abs_path = os.path.abspath(filepath)
        if not abs_path.startswith(self.root_dir):
            print(f"Error: Attempted to access file '{abs_path}' outside of project directory '{self.root_dir}'.")
            return False

        # 2. Check if the file matches any of the protected patterns.
        for pattern in self.protected_patterns:
            if fnmatch.fnmatch(os.path.basename(filepath), pattern):
                print(f"Error: Attempted to write to protected file '{filepath}'.")
                return False

        return True

    def read(self, filepath: str) -> str:
        """Reads a file's content."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def write(self, filepath: str, content: str):
        """
        Writes content to a file after performing safety checks.
        Raises PermissionError if the write operation is not allowed.
        """
        if self._is_path_safe(filepath):
            try:
                # --- Start of fix ---
                # Only try to create directories if the path includes them.
                directory = os.path.dirname(filepath)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                # --- End of fix ---

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Successfully wrote to '{filepath}'.")
            except Exception as e:
                print(f"Error writing to file '{filepath}': {e}")
                raise
        else:
            raise PermissionError(f"Write access denied for file: {filepath}")