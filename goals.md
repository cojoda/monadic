# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Refactor the agent's prompting mechanism to conditionally include API documentation as context. The prompt construction methods in `improver.py` must be updated to check if `llm_provider.py` is one of the files being edited for the current task. If it is, the methods should read documentation from a `docs/` directory and inject it into the prompt. If not, the documentation should be omitted to save tokens and improve focus. This entire task must be completed without editing any of the files listed in `protected.yaml`.