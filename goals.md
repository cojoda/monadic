# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Implement autonomous test quarantining.

This involves updating `improver/orchestrator.py`: Inside the `Improver.run` method's test failure logic, add a new condition. If the `TestFailureAnalysisTask` returns a `test_flaw` verdict, the system must:
1.  Immediately add the faulty test's name to a `quarantined_tests.json` file within the target project directory.
2.  Re-run the test suite, excluding any quarantined tests.
3.  If the remaining tests pass, proceed to apply the original code changes.
4.  Print a clear WARNING listing any tests that were quarantined.