# self_improver.py
import argparse
import asyncio
from improver import Improver
from safe_io import SafeIO

def get_active_goal(goals_file: str) -> str:
    '''Parses goals.md to get the first short-term goal.'''
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
            if stripped_line.startswith('- ') and not is_collecting_goal:
                is_collecting_goal = True
                goal_lines.append(stripped_line[2:])
                continue
            if is_collecting_goal:
                if stripped_line.startswith('- ') or stripped_line.startswith('##'):
                    break
                if not stripped_line:
                    goal_lines.append("")
                else:
                    goal_lines.append(stripped_line)

    if goal_lines:
        return "\n".join(goal_lines).strip()
    raise ValueError(f"No short-term goal found in {goals_file}")

async def main():
    '''The main entry point for the self-improving agent.'''
    parser = argparse.ArgumentParser(
        description="A self-improving code generator.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--project-dir',
        type=str,
        required=True,
        help="The path to the project directory to be improved."
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

    # Instantiate core components.
    safe_io = SafeIO(project_dir=args.project_dir)
    # Pass branch and iteration counts to the constructor.
    improver = Improver(
        safe_io,
        default_num_branches=args.branches,
        default_iterations_per_branch=args.iterations
    )

    # The run method now only needs the goal.
    await improver.run(goal=active_goal)

if __name__ == "__main__":
    asyncio.run(main())