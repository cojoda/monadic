import argparse
import asyncio

from improver import Improver
from safe_io import SafeIO

def get_active_goal(goals_file: str) -> str:
    """Parses goals.md to get the first short-term goal."""
    with open(goals_file, 'r') as f:
        lines = f.readlines()

    in_short_term_section = False
    for line in lines:
        if line.strip().lower() == "## short term":
            in_short_term_section = True
            continue
        if in_short_term_section:
            if line.strip().startswith('- '):
                # Return the first bullet point found
                return line.strip()[2:]
    
    raise ValueError("No short-term goal found in goals.md")

async def main():
    """
    The main entry point for the self-improving agent.
    """
    parser = argparse.ArgumentParser(
        description="A self-improving code generator.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--file',
        required=True,
        help="The path to the file to be improved."
    )
    parser.add_argument(
        '--branches',
        type=int,
        default=3,
        help="The number of parallel improvement branches to run."
    )
    args = parser.parse_args()

    try:
        active_goal = get_active_goal('goals.md')
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: Could not load goal. {e}")
        return

    # Instantiate core components
    safe_io = SafeIO()
    improver = Improver(safe_io)

    # Run the improvement process
    await improver.run(
        goal=active_goal,
        file_path=args.file,
        num_branches=args.branches
    )

if __name__ == "__main__":
    asyncio.run(main())