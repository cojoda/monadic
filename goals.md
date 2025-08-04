# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Implement a safety guardrail to prevent protected files from being included in the agent's working context. The `run` method in `improver.py` must be updated to filter the incoming `file_paths` list, ignoring any files that are listed in `protected.yaml`. This ensures that protected files are never read, passed to the LLM, or considered for editing. **This entire task must be completed without editing any of the files listed in `protected.yaml`.**