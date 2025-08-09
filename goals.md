# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- In improver/models.py, create a new Pydantic model named WorkflowContext. It should have fields to hold the goal (str), file_tree (List[str]), and an empty scaffolding_plan (Optional[ScaffoldingPlan]). This will be the foundation for our centralized state.