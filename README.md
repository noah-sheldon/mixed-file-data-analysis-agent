# Build a multi-format data analysis agent

A runnable starter for a YouTube live stream: ingest CSV, XLSX, PDF, and DOCX files; answer with exact table queries plus cited document evidence; compare LangGraph and LlamaIndex over the same tools; finish with an evaluation and performance plan.

## Recommendation

An agent framework is **not required** for the first version. Start with plain Python ingestion and guarded data tools; add a model tool loop only if tool choice helps. Use **LangGraph when** you need explicit routing, state, retries, checkpoints, or human approval. Keep the LlamaIndex adapter as the stream comparison. Deep Agents is built on LangGraph; it adds planning, context management, filesystem support, and subagents for long-horizon, open-ended work. Consider it when users need an autonomous investigation that produces reports or delegates follow-up analyses. It is a higher-level harness, not a replacement for the parser pipeline or warehouse permissions. This is a fit-based recommendation from current official docs, not a universal benchmark claim.

The wider landscape includes CrewAI (role-oriented Crews and deterministic Flows), OpenAI Agents SDK (agent loop, handoffs, guardrails, tracing), Microsoft Agent Framework (the documented successor to AutoGen and Semantic Kernel), Google ADK, Haystack, and Pydantic AI. See [`research/frameworks-and-warehouse.md`](research/frameworks-and-warehouse.md) for the comparison and primary sources. The repo implements LangGraph and LlamaIndex adapters so the live stream stays focused; the other frameworks are evaluated as options, not represented as working adapters.

Do not send every file to an LLM. Load CSV/XLSX into DuckDB for exact math. Extract PDF/DOCX text into source-located passages for search. At hundreds of files, keep originals and a hash/version manifest in object storage; incrementally ingest to raw/bronze and validated/silver layers, then expose curated/gold tables or a semantic layer to the agent. Keep document chunks in a search index with page/heading, source, checksum, and ACL metadata. Route each question to the warehouse metric/SQL tool, document search, or both. The sample lexical retrieval is deliberately a baseline; measure it before choosing a vector/hybrid index. The local demo does not model production concurrency or governance.

## Quick start

```bash
cd data-analysis-agent-stream
python -m venv .venv
source .venv/bin/activate
pip install -e '.[notebook]'
jupyter lab
```

Open `notebooks/live_demo.ipynb`, set the data folder to `data/sample`, and run the cells. Ingestion and local SQL tools work without an API key. The framework agents need `OPENAI_API_KEY` and the respective extra:

```bash
pip install -e '.[langgraph]'
pip install -e '.[llamaindex]'
```

For a LangGraph run, use `build(".data-agent/demo.duckdb").invoke({"messages": [{"role": "user", "content": "Which region generated the most revenue, and what explains it?"}]})`. For LlamaIndex, call `await build(".data-agent/demo.duckdb").run(user_msg="Which region generated the most revenue, and what explains it?")` from an async notebook cell.

## Formats and boundaries

| Input | Demo path | Production consideration |
|---|---|---|
| CSV | DuckDB CSV reader → one table | Detect schema drift, encoding, delimiters, and very wide files |
| XLSX | pandas/openpyxl → one DuckDB table per sheet | Define policies for hidden sheets, formulas, merged cells, and huge workbooks |
| PDF | pypdf text per page | Scanned PDFs need OCR; tables/layout may need a layout-aware parser such as Docling |
| DOCX | python-docx paragraphs and tables | Preserve heading/table structure and source locations |

The local demo reloads the folder on each run. It is not a production bulk-ingestion service. For hundreds of files, add a manifest keyed by file hash and parser version, a durable queue, bounded worker concurrency, object storage for originals/normalized output, retries and dead-letter handling, tenant access controls, and incremental index updates. Measure actual file sizes and formats before promising throughput.

## Evals and performance

Start with the fixed cases in `evals/cases.json`. Record expected answer, relevant evidence, expected tool route, and source files. Track:

- **Correctness:** exact SQL result equality; citation/source accuracy; answer groundedness; abstention when no evidence exists.
- **Retrieval:** recall@k and context precision on document questions.
- **Agent behavior:** tool-call accuracy, completion rate, and unnecessary tool calls.
- **Performance:** p50/p95 end-to-end latency, parse throughput by file type, query latency, tokens and cost per question, memory, and failure/retry rates.

Run the plain baseline and both framework adapters over the same test cases, model, prompt, tools, and budgets. Compare cost/latency and quality; do not infer a framework winner from a tiny live demo. Keep deterministic SQL assertions separate from LLM-judge metrics. Ragas offers retrieval, faithfulness, and tool-use metrics; use them as signals alongside labeled examples, not as a substitute for correctness checks.

## Files

- `slides/index.html` — self-contained, keyboard-navigable stream deck; press `?` for controls and print to PDF.
- `notebooks/live_demo.ipynb` — visible, cell-by-cell stream walkthrough.
- `src/data_agent/` — ingestion, local query/search tools, and optional framework adapters.
- `evals/cases.json` — starter golden cases for exact and grounded answers.
- `research/frameworks-and-warehouse.md` — expanded framework landscape, public company case studies, Deep Agents decision, warehouse architecture, and sources.

## Sources

- Start simple: [Anthropic’s agent design guidance](https://www.anthropic.com/research/building-effective-agents).
- LangGraph and Deep Agents: [LangGraph multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent), [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api), [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview).
- LlamaIndex workflows and multi-agent patterns: [Workflows introduction](https://developers.llamaindex.ai/python/llamaagents/workflows/), [multi-agent patterns](https://developers.llamaindex.ai/python/framework/understanding/agent/multi_agent/).
- Framework options: [CrewAI docs](https://github.com/crewAIInc/crewAI/tree/main/docs), [OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents/sdk), [Microsoft Agent Framework](https://learn.microsoft.com/agent-framework/overview), [Google ADK](https://google.github.io/adk-docs/), [Haystack](https://docs.haystack.deepset.ai/docs/intro), [Pydantic AI](https://pydantic.dev/docs/ai/overview/).
- Document parsing options: [Docling supported formats](https://docling-project.github.io/docling/usage/supported_formats/), [Docling batch conversion](https://docling-project.github.io/docling/reference/document_converter/).
- Company case studies: [Spotify](https://engineering.atspotify.com/2026/06/encoding-your-domain-expert-the-context-layer-behind-spotifys-data-assistant), [OpenAI](https://openai.com/index/inside-our-in-house-data-agent/), [incident.io](https://incident.io/blog/agentic-data-analyst-pt-i), [Uber QueryGPT](https://www.uber.com/us/en/blog/query-gpt/), [Kensho / S&P Global](https://www.langchain.com/blog/customers-kensho), [LangChain GTM Deep Agent](https://www.langchain.com/blog/how-we-built-langchains-gtm-agent).
- Warehouse patterns: [medallion layers](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion), [Snowflake Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents), [BigQuery data agents](https://docs.cloud.google.com/bigquery/docs/create-data-agents), [Databricks Genie Agents](https://docs.databricks.com/aws/en/genie-agents/tune-quality/), [dbt Semantic Layer](https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl).
- Evaluation: [Ragas metrics](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/), [Ragas evaluation quickstart](https://docs.ragas.io/en/stable/getstarted/rag_eval/).
- Exact tabular queries: [DuckDB Python API](https://duckdb.org/docs/stable/clients/python/overview).

