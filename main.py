#!/usr/bin/env python3
"""
HIVE — Autonomous Swarm Intelligence Engine.

CLI:
    python main.py --goal "Evaluate this trading strategy"

Server (UI):
    python main.py --serve
"""

import os
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from memory import list_runs, load_json, RUNS_DIR


def main():
    parser = argparse.ArgumentParser(
        description="RealWorld Simulator — Multi-agent future simulation engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--goal", type=str, help="Your goal or scenario to analyze")
    parser.add_argument("--constraints", type=str, default="", help="Constraints (solo, runway, location)")
    parser.add_argument("--timeline", type=str, default="", help="Timeline horizon")
    parser.add_argument("--risk", type=str, default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--model", type=str, default=None, help="Override model")
    parser.add_argument("--serve", action="store_true", help="Start desktop UI server")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    parser.add_argument("--list-runs", action="store_true", help="List past runs")
    parser.add_argument("--show-run", type=str, default=None, help="Show a past run")

    args = parser.parse_args()

    if args.serve:
        from server import serve
        serve(host=args.host, port=args.port)
        return

    if args.list_runs:
        runs = list_runs()
        if not runs:
            print("No past runs found.")
        else:
            print("Past runs:")
            for r in runs:
                v = load_json(RUNS_DIR / r, "verdict.json") or {}
                prob = v.get("overall_success_probability", "?")
                goal = v.get("goal", "")[:50]
                print(f"  {r} — {goal} [{prob}]")
        return

    if args.show_run:
        run_dir = RUNS_DIR / args.show_run
        if not run_dir.exists():
            print(f"Run '{args.show_run}' not found.")
            return
        verdict = load_json(run_dir, "verdict.json") or {}
        print(json.dumps(verdict, indent=2))
        return

    # Interactive mode
    if not args.goal:
        print("=" * 50)
        print("  RealWorld Simulator")
        print("=" * 50)
        print()
        args.goal = input("What's your goal? ").strip()
        if not args.goal:
            print("No goal provided. Exiting.")
            sys.exit(1)
        args.constraints = input("Constraints? [Enter to skip]: ").strip()
        args.timeline = input("Timeline? [Enter to skip]: ").strip()
        print()

    api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("[ERROR] LLM_API_KEY not found in .env (or DEEPSEEK_API_KEY for backward compat)")
        sys.exit(1)

    # Run via server API (local)
    print("[main] Starting local run...")
    import asyncio
    from orchestrator import run_orchestration_stream

    async def run():
        from search import init_browser, close_browser, search_web
        try:
            await init_browser()
            await run_orchestration_stream(
                goal=args.goal,
                constraints=args.constraints,
                timeline=args.timeline,
                risk_tolerance=args.risk,
                model=args.model or None,
                search_fn=search_web,
            )
        finally:
            await close_browser()

    asyncio.run(run())

    # Show latest report
    runs = list_runs()
    if runs:
        report_path = RUNS_DIR / runs[0] / "report.md"
        if report_path.exists():
            print(f"\nReport: {report_path}")
            print(report_path.read_text()[:2000])


if __name__ == "__main__":
    main()
