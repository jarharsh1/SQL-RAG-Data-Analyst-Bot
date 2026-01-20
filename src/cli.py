#!/usr/bin/env python3
"""
CLI Tool for SQL + RAG Data Analyst Bot.

Usage:
    python src/cli.py "What was revenue by region last quarter?"
    python src/cli.py --interactive
"""

import argparse
import sys
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from src.agent.graph import create_analyst_agent
from src.models.schemas import QueryRequest

console = Console()


def format_response(response: dict) -> None:
    """Format and display query response."""
    final_response = response.get("response")

    if not final_response:
        console.print("[red]Error: No response generated[/red]")
        return

    # Display answer
    console.print(
        Panel(
            final_response.answer,
            title="[bold cyan]Answer[/bold cyan]",
            border_style="cyan",
        )
    )

    # Display SQL (if available and requested)
    if final_response.transparency and final_response.transparency.sql_executed:
        console.print("\n[bold yellow]SQL Query:[/bold yellow]")
        syntax = Syntax(
            final_response.transparency.sql_executed,
            "sql",
            theme="monokai",
            line_numbers=True,
        )
        console.print(syntax)

    # Display data table (if available)
    if final_response.data and final_response.data.data:
        console.print(f"\n[bold green]Results ({final_response.data.row_count} rows):[/bold green]")

        # Create rich table
        table = Table(show_header=True, header_style="bold magenta")

        # Add columns
        for col in final_response.data.columns:
            table.add_column(col)

        # Add rows (limit to first 20 for display)
        display_limit = min(20, len(final_response.data.data))
        for row in final_response.data.data[:display_limit]:
            table.add_row(*[str(row.get(col, "")) for col in final_response.data.columns])

        console.print(table)

        if final_response.data.row_count > display_limit:
            console.print(
                f"[dim]... and {final_response.data.row_count - display_limit} more rows[/dim]"
            )

    # Display metadata
    console.print(
        f"\n[dim]Execution time: {final_response.metadata.execution_time_ms:.0f}ms | "
        f"Rows: {final_response.metadata.rows_returned}[/dim]"
    )

    # Display transparency (if available)
    if final_response.transparency:
        if final_response.transparency.definitions_used:
            console.print("\n[bold blue]Metric Definitions Used:[/bold blue]")
            for metric in final_response.transparency.definitions_used:
                console.print(f"  • {metric.name}: {metric.formula}")

        if final_response.transparency.assumptions:
            console.print("\n[bold blue]Assumptions:[/bold blue]")
            for assumption in final_response.transparency.assumptions:
                console.print(f"  • {assumption}")

    # Display error (if any)
    if final_response.error:
        console.print(f"\n[red]Error: {final_response.error}[/red]")


def query_analyst(question: str, user_id: str = "cli-user") -> None:
    """Query the analyst and display results."""
    console.print(f"[cyan]Question:[/cyan] {question}\n")

    # Create agent
    with console.status("[bold green]Thinking...", spinner="dots"):
        try:
            agent = create_analyst_agent()

            # Execute query
            result = agent.invoke({
                "question": question,
                "user_id": user_id,
                "show_sql": True,
                "show_transparency": True,
            })

            # Display response
            format_response(result)

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            sys.exit(1)


def interactive_mode() -> None:
    """Run in interactive mode."""
    console.print(
        Panel.fit(
            "[bold cyan]SQL + RAG Data Analyst - Interactive Mode[/bold cyan]\n"
            "Type your questions below. Type 'exit' or 'quit' to end session.",
            border_style="cyan",
        )
    )

    # Create agent once for all queries
    agent = create_analyst_agent()
    user_id = f"cli-user-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    while True:
        try:
            question = console.input("\n[bold green]❯[/bold green] ").strip()

            if not question:
                continue

            if question.lower() in ["exit", "quit", "q"]:
                console.print("[cyan]Goodbye![/cyan]")
                break

            # Execute query
            with console.status("[bold green]Thinking...", spinner="dots"):
                try:
                    result = agent.invoke({
                        "question": question,
                        "user_id": user_id,
                        "show_sql": True,
                        "show_transparency": True,
                    })

                    # Display response
                    console.print()
                    format_response(result)

                except Exception as e:
                    console.print(f"[red]Error: {str(e)}[/red]")

        except KeyboardInterrupt:
            console.print("\n[cyan]Goodbye![/cyan]")
            break
        except EOFError:
            console.print("\n[cyan]Goodbye![/cyan]")
            break


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="SQL + RAG Data Analyst - Query your data in natural language"
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Question to ask the analyst",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "-u",
        "--user-id",
        default="cli-user",
        help="User ID for audit logging",
    )

    args = parser.parse_args()

    # Show banner
    console.print(
        Panel.fit(
            "[bold purple]SQL + RAG Data Analyst[/bold purple]\n"
            "[dim]AI-powered data analysis with transparency[/dim]",
            border_style="purple",
        )
    )

    if args.interactive:
        interactive_mode()
    elif args.question:
        query_analyst(args.question, args.user_id)
    else:
        console.print("[yellow]Please provide a question or use --interactive mode[/yellow]")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
