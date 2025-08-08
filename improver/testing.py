from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from .core import LLMTask


class TestFailureAnalysis(BaseModel):
    # verdict: one of 'application_code_bug', 'test_flaw', 'unknown'
    verdict: str
    confidence: str
    explanation: str
    suggested_fix: Optional[str] = None


class TestFailureAnalysisTask(LLMTask):
    """LLM task to analyze a failing pytest run and the failing test source.

    Inputs to execute():
      - pytest_output: str  (combined stdout/stderr from pytest)
      - test_file_path: Optional[str] (path to the failing test file, if available)
      - test_source: Optional[str] (source code of the failing test file)

    Returns a TestFailureAnalysis pydantic model describing whether the failure
    is caused by application code or a flawed test, with explanation and a
    suggested fix where possible.
    """

    system_prompt = (
        "You are an expert Python engineer experienced in testing and debugging.\n"
        "Given the output of a failing pytest run and the source code of the failing test,\n"
        "determine whether the test failed due to a bug in the application code or due to a flaw in the test itself.\n"
        "Your response MUST be a JSON object matching the TestFailureAnalysis schema exactly and should contain only JSON.\n"
        "Fields:\n"
        "- verdict: one of 'application_code_bug', 'test_flaw', or 'unknown'\n"
        "- confidence: one of 'low', 'medium', 'high'\n"
        "- explanation: a concise explanation of your reasoning\n"
        "- suggested_fix: an optional short suggestion to fix the issue\n"
    )

    response_model = TestFailureAnalysis

    def construct_prompt(self, pytest_output: str, test_file_path: Optional[str] = None, test_source: Optional[str] = None) -> List[Dict[str, str]]:
        lines = [f"**Goal:** Determine whether a failing pytest run indicates an application bug or a flawed test."]
        lines.append("\n**Pytest Output (raw):**\n")
        # Keep the output but limit length to avoid extremely long prompts
        po = (pytest_output or '')
        if len(po) > 20000:
            po = po[-20000:]
            lines.append("<truncated tail of pytest output>\n")
        lines.append(po)

        if test_file_path:
            lines.append(f"\n**Failing test file path:** {test_file_path}\n")
        if test_source:
            lines.append("\n**Failing test source:**\n")
            lines.append(test_source)

        # Ask for structured JSON only
        lines.append("\nPlease return a single JSON object matching the TestFailureAnalysis schema with no extra commentary.")

        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": "\n".join(lines)}
        ]
