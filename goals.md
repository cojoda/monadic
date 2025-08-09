# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Implement autonomous self-correction for faulty tests.

This involves updating `improver/orchestrator.py` with the following logic:
1.  In the test failure block, add a new condition to handle the `test_flaw` verdict from the `TestFailureAnalysisTask`.
2.  When a test is identified as flawed, the system must **pause the current goal** and initiate a new, high-priority improvement loop with a specific objective, for example: "Fix the broken test in `tests/test_example.py`."
3.  The context for this new loop should include the code of the feature being tested, the source code of the faulty test, and the analysis explaining why the test is flawed.
4.  The agent will then attempt to fix its own test. After applying the fix, it will re-run the *entire* test suite.
5.  **If the fixed test passes** (and no other regressions are introduced), the agent will consider the correction successful and will then **resume its original goal**.
6.  **Deadlock Prevention**: If the agent fails to fix the test after **three consecutive attempts** (tracked by `improver/failure_log.py`), it should fall back to a quarantine mechanism. It will add the test to a `quarantined_tests.json` file, log a clear **WARNING** for the user, and then proceed with its original task, running against the remaining tests.