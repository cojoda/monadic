# self_improver.py (Corrected)
import argparse
import asyncio

# The import now correctly points to the library, not an application script.
from improver import Improver 
from safe_io import SafeIO

def get_active_goal(goals_file: str) -> str:
    '''Parses goals.md to get the first short-term goal, including multi-line descriptions.'''
    with open(goals_file, 'r') as f:
        lines = f.readlines()

    in_short_term_section = False
    is_collecting_goal = False
    goal_lines = []

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.lower() == "## short term":
            in_short_term_section = True
            continue

        if in_short_term_section:
            # Check for the start of the first bullet point
            if stripped_line.startswith('- ') and not is_collecting_goal:
                is_collecting_goal = True
                goal_lines.append(stripped_line[2:]) # Add the first line without the bullet
                continue

            if is_collecting_goal:
                # If we encounter a new bullet or a new section, we're done with the first goal.
                if stripped_line.startswith('- ') or stripped_line.startswith('##'):
                    break
                
                # If it's just an empty line, preserve it as a paragraph break.
                if not stripped_line:
                    goal_lines.append("") # Keep blank lines for formatting
                else:
                    # Otherwise, it's a continuation of the current goal
                    goal_lines.append(stripped_line)
    
    if goal_lines:
        # Join the collected lines back into a single string.
        return "\n".join(goal_lines).strip()

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