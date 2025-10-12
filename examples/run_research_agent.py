"""
Example: Running the ResearchAgent to ingest documents and query with RAG.

Usage:
  python examples/run_research_agent.py /path/to/docs "query text"
"""
from __future__ import annotations

import sys
from jarvis_core.agents.research import ResearchAgent


def main() -> None:
    docs = sys.argv[1] if len(sys.argv) > 1 else "."
    query = sys.argv[2] if len(sys.argv) > 2 else "what is contained?"
    agent = ResearchAgent()
    print(agent.execute(f"ingest {docs}", {}))
    print(agent.execute(f"query {query}", {"k": 5}))


if __name__ == "__main__":
    main()
