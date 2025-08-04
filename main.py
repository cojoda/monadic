# main.py (Now much leaner)
import asyncio
from safe_io import SafeIO
from improver import Improver # <-- Clean import from the package

if __name__ == "__main__":
    # This is an example for ad-hoc, manual execution.
    # To run this, you would execute: python main.py
    io = SafeIO()
    app = Improver(safe_io=io)
    # The goal can be provided directly here for testing.
    improvement_goal = "Add type hints to the run() method in improver/orchestrator.py"
    
    print(f"Running manual improvement with goal: {improvement_goal}")
    asyncio.run(app.run(goal=improvement_goal))