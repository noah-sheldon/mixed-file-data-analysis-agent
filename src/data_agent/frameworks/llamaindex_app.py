from __future__ import annotations

import os

from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent
from llama_index.llms.openai import OpenAI

from data_agent.ingest import list_tables, run_readonly_sql, search_documents


def build(database: str):
    def catalog() -> str:
        """List available tables and their columns."""
        return str(list_tables(database))

    def query(sql: str) -> str:
        """Run one read-only SELECT over known tables."""
        return str(run_readonly_sql(database, sql))

    def find_evidence(question: str) -> str:
        """Find passages in PDFs and Word documents; results include source locations."""
        return str(search_documents(database, question))

    analyst = FunctionAgent(
        name="analyst",
        description="Answers questions with exact tabular queries and cited document evidence.",
        system_prompt=(
            "Inspect the catalog before querying. Use document evidence for narrative claims. "
            "Cite source and location. Never invent results; state when evidence is missing."
        ),
        tools=[catalog, query, find_evidence],
        llm=OpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), temperature=0),
    )
    return AgentWorkflow(agents=[analyst], root_agent="analyst")

