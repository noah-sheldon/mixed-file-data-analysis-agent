# Build a multi-format data analysis agent

A runnable starter for a YouTube live stream: ingest CSV, XLSX, PDF, and DOCX files; answer with exact table queries plus cited document evidence; compare LangGraph and LlamaIndex over the same tools; finish with an evaluation and performance plan.

## Recommendation

Use **LangGraph as the first orchestration implementation** for this demo, and build the core once as framework-neutral Python tools. Add the LlamaIndex adapter as the comparison. LangGraph's explicit graph makes routing, retries, state, and checkpoints easy to show and control. LlamaIndex is a strong comparison when the center of gravity is data connectors, document retrieval, and its `AgentWorkflow` abstractions. This is a fit-based recommendation from the frameworks' official docs, not a universal benchmark claim.

Do not send every file to an LLM. Load CSV/XLSX into DuckDB for exact math. Extract PDF/DOCX text into source-located passages for search. At hundreds of files, route the question to the right data tool and retrieve a small evidence set. The sample lexical retrieval is deliberately a baseline; measure it before choosing a vector/hybrid index.

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

Run both framework adapters over the same test cases and model, prompt, tool definitions, and budgets. Compare cost/latency and quality; do not infer a framework winner from a tiny live demo. Keep deterministic SQL assertions separate from LLM-judge metrics. Ragas offers retrieval, faithfulness, and tool-use metrics; use them as signals alongside labeled examples, not as a substitute for correctness checks.

## Files

- `slides/index.html` — self-contained, keyboard-navigable stream deck; press `?` for controls and print to PDF.
- `notebooks/live_demo.ipynb` — visible, cell-by-cell stream walkthrough.
- `src/data_agent/` — ingestion, local query/search tools, and optional framework adapters.
- `evals/cases.json` — starter golden cases for exact and grounded answers.

## Sources

- LangGraph multi-agent patterns and graph primitives: [LangChain multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent), [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api), [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence).
- LlamaIndex workflows and multi-agent patterns: [Workflows introduction](https://developers.llamaindex.ai/python/llamaagents/workflows/), [multi-agent patterns](https://developers.llamaindex.ai/python/framework/understanding/agent/multi_agent/).
- Document parsing options: [Docling supported formats](https://docling-project.github.io/docling/usage/supported_formats/), [Docling batch conversion](https://docling-project.github.io/docling/reference/document_converter/).
- Evaluation: [Ragas metrics](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/), [Ragas evaluation quickstart](https://docs.ragas.io/en/stable/getstarted/rag_eval/).
- Exact tabular queries: [DuckDB Python API](https://duckdb.org/docs/stable/clients/python/overview).

