# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Make the IntegrationRunner file-type aware.

This involves one final change:
1.  Modify the `run` method in `improver/integration.py`. The syntax check must be updated to only parse files with a `.py` extension. Files without a `.py` extension should be skipped by the syntax check.