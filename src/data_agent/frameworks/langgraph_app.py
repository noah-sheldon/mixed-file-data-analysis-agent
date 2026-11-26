from __future__ import annotations

import os

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI

from data_agent.ingest import list_tables, run_readonly_sql, search_documents


def build(database: str):
    @tool
    def catalog() -> list[dict[str, str]]:
        """List available tables and their columns."""
        return list_tables(database)

    @tool
    def query(sql: str) -> list[dict[str, object]]:
        """Run one read-only SELECT over known tables."""
        return run_readonly_sql(database, sql)

    @tool
    def find_evidence(question: str) -> list[dict[str, str]]:
        """Find relevant passages in PDFs and Word documents."""
        return search_documents(database, question)

    tools = [catalog, query, find_evidence]
    model = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), temperature=0).bind_tools(tools)

    def call_model(state: MessagesState):
        system = SystemMessage(content=(
            "You are a data analyst. Inspect the catalog before querying tables. "
            "Use document evidence for narrative claims. Cite source and location. "
            "Never invent results; state when evidence is missing."
        ))
        return {"messages": [model.invoke([system, *state["messages"]])]}

    graph = StateGraph(MessagesState)
    graph.add_node("analyst", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "analyst")
    graph.add_conditional_edges("analyst", tools_condition)
    graph.add_edge("tools", "analyst")
    return graph.compile()

