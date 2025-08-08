# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Implement test-driven correction by generating new goals for bug fixes.

This involves updating `improver/orchestrator.py`:
1.  After a test run, if the `TestFailureAnalysisTask` determines that the application code is buggy, the system must not apply the proposed changes.
2.  Instead, it must construct a new, detailed goal string that specifies which file and test failed, and what the error was. For example: "Fix the bug in `improver/orchestrator.py` that causes the test `tests/test_orchestrator.py::test_new_feature` to fail."
3.  The system will then print this new suggested goal to the console, prefixed with a clear message for the user, and then gracefully exit.