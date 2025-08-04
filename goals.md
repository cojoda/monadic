# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- The agent's current refactoring capability is unsafe because it does not respect file protections in the expanded context. This goal is to fix this by making the BranchTask aware of protected files.

In improver/branch.py, find the BranchRunner.run method. Locate the call to self.branch_task.execute(). Modify this call to pass the protected_files list, which is available as self.protected_files.
Still in improver/branch.py, update the BranchTask.construct_prompt method signature to accept a protected_files: List[str] argument.
Finally, modify the logic inside BranchTask.construct_prompt to use this new list. If the protected_files list is not empty, it must append a new, clearly marked section to the user prompt. This section should be titled "Protected Files" and explicitly state: "You can use the following files for context, but you MUST NOT include them in your 'edits' list." Then, list the protected files.