# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Make the system file-type aware to handle non-Python files correctly.

This involves the following steps:
1.  Modify `improver/ast_utils.py` in `get_local_dependencies` to only parse files with a `.py` extension. Other file types should be ignored.
2.  Modify `improver/branch.py` in the `BranchRunner.run` method to only perform syntax checking on files with a `.py` extension. Non-Python files should be passed through without validation.
3.  Update the `construct_prompt` in `improver/branch.py` to specify the language of the file in the prompt when presenting the file to the LLM. For example, instead of just `File to improve: pytest.ini`, it should say `File to improve: pytest.ini (ini)`.