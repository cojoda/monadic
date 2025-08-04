# Monadic Self-Improving Code Generator

## Long Term
- Evolve into a fully autonomous agent that can manage its own features, testing, and releases.
- Develop a sophisticated understanding of its own architecture to perform complex refactors.
- Optimize for cost, performance, and code quality based on high-level human guidance.

## Short Term
- Create a new planning and scaffolding capability in the empty file improver/planning.py. This file will define the new data contract and the agent responsible for creating it.
Inside improver/planning.py, create a new Pydantic model named ScaffoldingPlan. It must have two fields: reasoning (a string), existing_files_to_edit (a list of strings), and new_files_to_create (a list of strings).
In the same file, create a new PlanningAndScaffoldingTask class that inherits from LLMTask.
Its response_model must be the ScaffoldingPlan model.
Its system prompt should instruct an expert software architect to analyze a user's goal and the project file tree. Based on this, the architect must create a step-by-step plan in the reasoning field. It must then identify all existing project files that will need to be read or edited, and crucially, list all new files (like new modules or test files) that must be created from scratch to fulfill the goal.