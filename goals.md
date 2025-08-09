# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Implement a self-correction loop for the IntegrationRunner.

This involves updating `improver/integration.py` with the following logic:
1.  **Modify the `IntegrationRunner.run` method.** When a `SyntaxError` is detected in the integrated code, do not immediately exit. Instead, start a retry loop that can be attempted up to 2 times.
2.  **Capture and Pass Error Context.** Inside this loop, capture the file path and the specific `SyntaxError` message.
3.  **Update the `IntegratorTask.construct_prompt` method.** It must be updated to accept an optional `error_context` string. When this string is provided, it should be added to the prompt, instructing the LLM to fix the syntax error in its next integration attempt.
4.  **Re-run the Integration.** Call the `IntegratorTask` again with the original proposals and the new error context.
5.  **Fallback.** If the integration still fails after the maximum number of retries, only then should the runner abort and return `None`.