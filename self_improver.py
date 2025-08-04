# self_improver.py (Corrected)
import argparse
import asyncio

# The import now correctly points to the library, not an application script.
from improver import Improver 
from safe_io import SafeIO

def get_active_goal(goals_file: str) -> str:
    '''Parses goals.md to get the first short-term goal.'''
    # Your existing function works perfectly.
    with open(goals_file, 'r') as f:
        lines = f.readlines()
    in_short_term_section = False
    for line in lines:
        if line.strip().lower() == "## short term":
            in_short_term_section = True
            continue
        if in_short_term_section:
            if line.strip().startswith('- '):
                return line.strip()[2:]
    raise ValueError(f"No short-term goal found in {goals_file}")

async def main():
    '''
    The main entry point for the self-improving agent.
    '''
    parser = argparse.ArgumentParser(
        description="A self-improving code generator.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--branches',
        type=int,
        default=3,
        help="The number of parallel improvement branches to run."
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=1,
        help="The number of serial iterations to run per branch."
    )
    args = parser.parse_args()

    try:
        active_goal = get_active_goal('goals.md')
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: Could not load goal. {e}")
        return

    # Instantiate core components
    safe_io = SafeIO()
    improver = Improver(safe_io) # Instantiating the class from the library

    # The call is unchanged and correct
    await improver.run(
        goal=active_goal,
        num_branches=args.branches,
        iterations_per_branch=args.iterations
    )

if __name__ == "__main__":
    asyncio.run(main())