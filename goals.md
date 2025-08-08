# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Implement the Test Failure Analysis task.

This goal has two parts:
1.  Create a new file, `improver/testing.py`, which will contain a new `TestFailureAnalysisTask`. This LLM task will take the output of a failing `pytest` run and the source code of the failing test as input. It should determine whether the test failed due to a bug in the application code or a flaw in the test itself.
2.  Update `improver/orchestrator.py` to call this new task whenever a test fails. The result of the analysis should be printed to the console.