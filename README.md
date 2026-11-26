# Build a multi-format data analysis agent

A runnable starter for a YouTube live stream: ingest CSV, XLSX, PDF, and DOCX files; answer with exact table queries plus cited document evidence; compare LangGraph and LlamaIndex over the same tools; finish with an evaluation and performance plan.

## Recommendation

An agent framework is **not required** for the first version. Start with deterministic Python ingestion, access checks, query validation, and retrieval tools. For ordinary natural-language questions, add one bounded planner that returns `structured`, `documents`, `both`, or `clarify`; code enforces that choice and runs the permitted SQL/search tools. Add an adaptive agent loop only when the next step depends on tool results. Use **LangGraph when** explicit state, branching, retries, checkpoints, or human approval help. Deep Agents is built on LangGraph; it adds planning, context management, filesystem support, and subagents for long-horizon, open-ended investigations. It is a later autonomy option, not a replacement for the parser pipeline or warehouse permissions. See the routing decision and execution split in [`research/frameworks-and-warehouse.md`](research/frameworks-and-warehouse.md#which-steps-are-deterministic-and-which-use-an-agent).

Do not add more frameworks to the live bake-off. Compare the plain Python baseline and LangGraph using the same tools, model, and questions. Keep LlamaIndex as a data-centric alternative/demo, not a head-to-head performance winner; mention Deep Agents for the open-ended case. DSPy may be considered later for prompt/program optimization against evals, but it is not another agent runtime. The wider ecosystem—CrewAI, OpenAI Agents SDK, Microsoft Agent Framework, Google ADK, Haystack, and Pydantic AI—is covered in [`research/frameworks-and-warehouse.md`](research/frameworks-and-warehouse.md) but not all implemented here.

Do not send every file to an LLM. Load CSV/XLSX into DuckDB for exact math. Extract PDF/DOCX text into source-located passages for search. At hundreds of files, keep originals and a hash/version manifest in object storage; incrementally ingest to raw/bronze and validated/silver layers, then expose curated/gold tables or a semantic layer. Keep document chunks in a search index with page/heading, source, checksum, and ACL metadata. For each request, code authenticates and scopes access; a bounded planner chooses `structured`, `documents`, `both`, or `clarify`; code validates and executes the allowed tools; an agent loop is optional for adaptive investigations. The sample lexical retrieval is deliberately a baseline; measure it before choosing a vector/hybrid index. The local demo does not model production concurrency or governance.

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

The current adapters intentionally show a simple model-directed tool loop so viewers can compare framework APIs over shared tools. They do not yet implement the recommended bounded `structured | documents | both | clarify` planner. Treat the adapters as teaching/demo code, not a production routing or authorization layer. The recommended separation and route cases are documented in the research brief and `evals/cases.json`.

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
- `docs/system-design.mmd` — editable Mermaid source for the ingestion and question-answer architecture diagrams.
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

