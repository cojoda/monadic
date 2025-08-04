# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Enable multi-file editing capabilities. The agent's core logic in `improver.py` must be refactored to handle a list of files instead of a single file path. This includes updating the LLM prompts to accept multiple file contexts and redesigning the Pydantic schema to support a list of file edits, where each edit specifies a `file_path` and its new `code`. This is the first step towards allowing the agent to modify both application code and test code in the same run.