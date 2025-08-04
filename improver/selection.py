# improver/selection.py
from typing import List, Dict
from .core import LLMTask
from .models import FileSelectionResponse

class FileSelectionTask(LLMTask):
    system_prompt = (
        'You are an expert Python programmer tasked with selecting files relevant to a specified goal from a provided file tree.'
        ' You must strictly NOT select any protected files listed.'
        ' Respond with a JSON object with key "selected_files" containing an array of file paths.'
        ' Respond ONLY with the JSON object, no extra text.'
    )
    response_model = FileSelectionResponse

    def construct_prompt(self, file_tree: List[str], protected_files: List[str]) -> List[Dict[str, str]]:
        prompt_lines = [
            f'**Goal:** {self.goal}',
            '\nYou have the following project file tree (one file path per line):',
            *file_tree,
            '\nThe following files are PROTECTED and must NOT be selected:',
            *protected_files,
            '\nBased on the goal, select only relevant files not listed as protected.'
            ' Respond ONLY with a JSON object with key ' + "'selected_files'" + ' listing file paths.'
        ]
        return [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": "\n".join(prompt_lines)}]