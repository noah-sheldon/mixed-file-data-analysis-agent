# Framework and warehouse research

Reviewed 26 November 2026. This is a fit comparison from current primary documentation, not a market-share ranking or an independent performance benchmark. Vendor docs explain product capabilities; they do not establish which framework has the most users or is fastest for this workload.

## Is an agent framework needed?

No, not by default. Start with a small Python service or CLI that exposes narrow functions: discover files, ingest/normalize, inspect a catalog, run a guarded query, search document passages, and format cited output. Add an LLM tool loop only if choosing among those tools materially helps users. Use plain Python control flow for known steps. Add a workflow runtime when state, conditional branches, retries, interrupts, or durable multi-step execution are real requirements. Add a more autonomous harness only for open-ended work where the next step depends on what earlier analysis finds.

This matches Anthropic's published guidance: start with the simplest solution; workflows suit predictable tasks; agents suit tasks that need model-directed flexibility; a framework can help with common orchestration but can also add abstraction and debugging cost. It is advice, not a law, and the post notes the ecosystem has changed since its original publication. [Anthropic: Building effective agents](https://www.anthropic.com/research/building-effective-agents).

For this product, a plain tool-calling agent or a small LangGraph graph is enough for “find revenue and explain the change.” The data ingestion pipeline should be a separate deterministic service. “There are 200 files” increases the ingestion, catalog, access-control, and context-selection work; it does not itself require Deep Agents or multiple runtime agents.

## What public teams describe building

These are engineering/product teams reporting their own systems. Treat adoption and accuracy numbers as self-reported; the posts are useful architectural case studies, not independent head-to-head benchmarks.

### Spotify: curated domains over a very large warehouse

Spotify describes a data assistant across 70,000+ datasets and petabytes. It routes each request to a domain “cluster” owned by domain experts. A cluster contains relevant warehouse datasets with profiling and common values, vetted question-to-SQL pairs, and business documentation. The assistant queries the warehouse and returns the answer with SQL and sources. Spotify reports that curators accepted only 12.5% of auto-proposed historical-query examples. The lesson is to use query history as candidate material, then have people validate business meaning. [Spotify Engineering](https://engineering.atspotify.com/2026/06/encoding-your-domain-expert-the-context-layer-behind-spotifys-data-assistant).

### OpenAI: offline context enrichment, live warehouse analysis

OpenAI describes an internal data agent for more than 70,000 datasets. It enriches metadata from table usage, human annotations, transformation code and lineage, then uses retrieval to supply only relevant context at runtime. Institutional documents are stored with permission metadata; live warehouse queries handle current facts. The agent can iterate on its analysis and publish notebooks/reports. The post emphasizes the quality/evaluation loop and permissions. This is the closest public analogue for a later, more open-ended analyst experience; it does not imply the first version needs that much autonomy. [OpenAI Engineering](https://openai.com/index/inside-our-in-house-data-agent/).

### incident.io: one gated query tool and progressively loaded guidance

incident.io describes domain “themes” containing analyst guidance and vetted question/SQL examples. It hydrates only the relevant schema. One query tool is the only code with a BigQuery connection; it dry-runs SQL, validates statement type and table allowlists, rejects expensive scans, and logs success/rejection/failure. The team audits stale examples, missing coverage, overlapping route phrases, and context size. This is a useful minimum production pattern for a warehouse-backed data analyst. [incident.io engineering](https://incident.io/blog/agentic-data-analyst-pt-i).

### Uber: filter context before asking the SQL model

Uber's QueryGPT post says its early similarity search over schema and SQL examples lost accuracy as it onboarded more tables. It introduced business-domain workspaces and an intent step to narrow which schemas/examples the model sees, then table and column selection and evaluation. The post notes large schemas (over 200 columns) could consume 40–60k tokens at the time. The transferable point is not “add many agents”: it is to retrieve the correct domain context before generation and measure SQL outcomes. [Uber Engineering: QueryGPT](https://www.uber.com/us/en/blog/query-gpt/).

### Kensho/S&P Global: shared routing and retrieval protocol

Kensho describes a LangGraph router above domain-owned specialist retrieval agents, unifying structured and unstructured data access behind a common response protocol with provenance. It evaluates routing, selected tools, retrieved data quality, and answer completeness. This is a case where multi-agent routing makes sense because the product spans independent business domains and products. [Kensho/LangChain case study](https://www.langchain.com/blog/customers-kensho).

### LangChain GTM: a Deep Agents fit

LangChain describes using Deep Agents for its own account research and follow-up system because the steps were long-running and inputs varied in size and structure across CRM, call notes, and web sources. It used planning and a virtual filesystem to manage large tool outputs, and subagents for independent account research. It started with representative evaluations and rule checks. That resembles open-ended research and report generation much more than a bounded SQL+document answer. This is a company-authored case study, not a general Deep Agents benchmark. [How LangChain built its GTM agent](https://www.langchain.com/blog/how-we-built-langchains-gtm-agent).

### Cloud-native examples

Snowflake Cortex Agents can call Cortex Analyst over semantic views for structured queries and Cortex Search for unstructured evidence within Snowflake's privilege model. BigQuery data agents can be scoped to curated tables/views/UDFs with metadata, instructions, example questions, and IAM-based permissions. Databricks Genie Agents use governed Unity Catalog assets and can be improved with example SQL and trusted assets. If one platform already stores the company's data, evaluate its managed agent before building another cross-platform layer. [Snowflake Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents), [BigQuery data agents](https://docs.cloud.google.com/bigquery/docs/create-data-agents), [Databricks Genie quality guidance](https://docs.databricks.com/aws/en/genie-agents/tune-quality/).

## Recommendation for the livestream build

Teach **three implementation levels**, while keeping one set of data tools and eval cases:

1. **Plain Python baseline:** deterministic file ingestion, catalog, SQL validator and search function; optionally one model tool loop. This tests whether an agent is even needed.
2. **LangGraph workflow:** add explicit state/routing/checkpoints when requests need a fixed, inspectable sequence. This is the best framework demo for showing control.
3. **Deep Agents experiment:** make a separate branch or notebook cell for an investigation-style prompt that can plan, revisit evidence, use persistent workspace, and create a report. Deep Agents is built on LangGraph, so present it as a higher-level harness/autonomy choice, not another unrelated graph engine.

Mention LlamaIndex as the data-centric alternative and CrewAI as a role/Flow-oriented alternative in the comparison slide, but avoid implementing four frameworks in the livestream. Keep the ranking fair: same model, question set, source tools, authorization, output schema, and cost/time ceilings. Record tool traces and score exact SQL results, citations, grounded claims, abstention, latency and cost. One properly constrained workflow is a stronger lesson than a large agent cast.

## Framework landscape

| Option | What it is useful for | Fit for this data analyst |
|---|---|---|
| **LangGraph** | Explicit stateful graphs, routing, loops, persistence, and human checkpoints. | Strong first custom implementation: make SQL and evidence retrieval explicit steps, with a bounded agent node. |
| **Deep Agents** | A prebuilt agent harness for long-horizon tasks, adding planning, filesystem-backed context, subagents, and context management on LangGraph. | Consider when users ask open-ended investigations that build artifacts, keep working context, or delegate independent research. It is built on LangGraph, not a competing runtime. |
| **LlamaIndex** | Data connectors, indexing/retrieval abstractions, and event-driven Workflows / AgentWorkflow. | Good alternative when the center of the application is document ingestion and retrieval. Keep warehouse tools independent of it. |
| **CrewAI** | Role-oriented Crews plus Flows for coordinating agent work with deterministic steps. | Useful for a stream comparison of role/delegation patterns; agent personas are not required for a single data question. |
| **OpenAI Agents SDK** | Tool loop, handoffs, guardrails, sessions, and built-in tracing around OpenAI's agent API. | A compact option when the model stack is OpenAI-centered; compare portability and governance needs against the chosen baseline. |
| **Microsoft Agent Framework** | Agent abstractions and explicit workflows, with state, middleware, telemetry, and human-in-the-loop patterns. Microsoft describes it as the successor to AutoGen and Semantic Kernel. | Worth evaluating for a .NET/Azure-aligned team or existing Microsoft investment. Treat AutoGen and Semantic Kernel as migration paths, not fresh default picks without checking the successor framework. |
| **Google ADK** | Multi-agent and workflow APIs, with Google Cloud deployment, evaluation, and observability tooling. | Strong candidate for a Google Cloud / Gemini stack; not a warehouse requirement. |
| **Haystack** | Composable components and deterministic pipelines, with agents available as a pipeline component. | Good fit when search/RAG pipeline composition and explicit components are central. |
| **Pydantic AI** | Typed Python agent interfaces and validation, plus separate graph/eval packages and provider integrations. | Worth testing if typed tool contracts and Python ergonomics matter more than a particular vendor workflow. |

### How to compare fairly

Compare frameworks by running the same labeled questions, shared tool functions, model, prompt, limits, and warehouse role. Score exact SQL result correctness, source/citation coverage, abstention, tool-call accuracy, latency, tokens/cost, and failure rate. A small show-and-tell is not a framework benchmark. Do not compare a simple tool loop with an unconstrained deep agent and attribute extra planning calls to “framework quality.”

### Is this a Deep Agent?

The first product should be a **LangGraph workflow with a bounded analyst agent inside it**:

1. Identify whether the question needs tables, documents, or both.
2. Call a catalog/semantic-metric tool and a read-only query tool for numeric analysis.
3. Call document search for narrative evidence.
4. Check results and citations; abstain when the evidence is absent.
5. Return the answer with reproducible query/source references.

The ordering, authorization, and query budgets are known in advance, so the application graph should own them. Deep Agents can be a separate experiment for a more open-ended prompt such as “investigate why churn rose, explore the relevant data and documents, create a report, then list follow-up analyses.” It adds useful planning/context/subagent capabilities, but those capabilities do not replace data ingestion, warehouse modeling, or SQL governance. A future version can call a Deep Agent from one bounded graph node if the task needs it.

## Data platform architecture for hundreds of mixed files

“Hundreds of files” is not a capacity specification by itself. A few hundred small spreadsheets differ greatly from a few hundred scanned, multi-hundred-page PDFs. Measure bytes, pages, sheets, schema variability, OCR share, and update frequency before sizing workers or choosing a platform.

### Keep the raw evidence, model the tables, index the prose

```text
CSV / XLSX ──> immutable object storage + file manifest
                     │
                     ├── Bronze: raw parsed tables and file/sheet lineage
                     ├── Silver: typed, cleaned, deduplicated tables
                     └── Gold: curated business models + governed metrics
                                      │
                                      └── SQL / semantic tool for the agent

PDF / DOCX ──> immutable object storage + file manifest
                     │
                     └── parse/OCR → chunks with page/heading + ACL metadata
                                      │
                                      └── lexical/vector search tool for the agent

Agent: route to SQL and/or document search; join using stable IDs and cite both.
```

Use a bronze/silver/gold or equivalent pattern as a logical quality progression, not as a mandate to create three copies for every tiny file. Preserve source IDs, checksums, parser versions, ingestion timestamps, and access rules. Reprocess only when the file or parser changes. A durable queue, bounded concurrency, retries, and a dead-letter view make a bulk run recoverable. Keep original PDFs/DOCX in object storage; index extracted chunks and provenance in a search store. Avoid placing every document's entire text in the warehouse or every spreadsheet row in a prompt.

For analyst questions, expose curated gold views or a semantic layer with metric definitions, synonyms, joins, and verified example questions. Do not make raw bronze tables the agent's default interface. Provide a least-privilege read-only identity; restrict schemas, columns, row scope, query duration/bytes, and result size; log generated SQL and its result reference. If sensitive rows require user-specific authorization, enforce that in the data platform, not in a prompt.

### Platform choices

- **Already have a warehouse?** Use it. Add file ingestion and a governed semantic surface there before adding a second platform.
- **DuckDB vs ClickHouse:** DuckDB is the local demo/default when one process needs to query normalized CSV/XLSX or Parquet with SQL and minimal operations. It is embedded, so the demo needs no database server. ClickHouse is a serious candidate when the application needs a shared OLAP service: high query concurrency, continuous append-heavy ingestion, large analytical tables, dashboards, or horizontal growth. It is also columnar and can run locally, so the distinction is deployment/workload fit, not that DuckDB cannot do analytics or that ClickHouse is only for “big data.” For this project, hundreds of office files alone do not establish the need for ClickHouse. Benchmark representative normalized data and a realistic mix of users/queries before switching. Neither engine replaces PDF/DOCX extraction, source provenance, authorization, or document retrieval.
- **Snowflake:** Cortex Agents can combine Cortex Analyst for structured queries via semantic views and Cortex Search for unstructured retrieval. The docs emphasize semantic descriptions and verified queries for SQL accuracy.
- **BigQuery:** Data agents are configured over selected knowledge sources with metadata/instructions/verified queries; permissions apply to agent access. The conversational analytics docs also describe using data agents with PDF-like object data. This is a natural fit if the team already runs GCP/BigQuery.
- **Databricks:** Genie Agents use Unity Catalog assets, instructions, example SQL, and knowledge snippets; the medallion pattern can move raw inputs toward validated and business-ready tables.
- **Local demo / early prototype:** DuckDB is enough to teach exact SQL on sample CSV/XLSX. It is not a claim about cloud concurrency, governance, or a production ingest service.

Choose among cloud warehouses using existing contracts, data residency, governance, workloads, and team skills; this prompt does not identify an existing cloud, so no vendor-specific deployment is assumed.

## Why document answers can arrive in seconds: parsing, indexing, caching

“It read my file in seconds” can describe several different paths. These stages should be measured separately:

1. **Parse / extract:** turn file bytes into text, tables, and (for vision-capable PDF paths) page images. Parsing behavior is product- and file-type-specific. OpenAI's Responses file-input guide says PDFs contribute extracted text plus page images; DOCX and other non-PDF documents contribute extracted text; spreadsheets use a spreadsheet-specific augmentation path that reads up to the first 1,000 rows per sheet and adds generated summary/header metadata. The guide recommends hosted shell for deep spreadsheet operations such as joins and aggregations. This makes a quick summary different from exhaustive analysis of an arbitrarily large workbook. [OpenAI file inputs](https://developers.openai.com/api/docs/guides/file-inputs)
2. **Upload / reference:** a persistent file ID can avoid sending the original bytes again. Anthropic's Files API is explicitly “upload once, reference by file_id” for Messages API requests; that is reusable storage/reference, not evidence that every file was pre-indexed into a searchable corpus. [Anthropic Files API](https://platform.claude.com/docs/en/build-with-claude/files)
3. **Index / retrieve:** for a corpus, ingest ahead of time, split/prepare searchable units, then fetch only relevant evidence for a question. OpenAI File Search requires files in a vector store before invoking search; this is the distinct large-corpus path instead of repeatedly passing entire files as input. [OpenAI File Search](https://developers.openai.com/api/docs/guides/tools-file-search)
4. **Model inference:** the model answers from the extracted or retrieved context. A quick first token/streamed answer does not mean the whole corpus was read or exhaustively computed.
5. **Prompt cache:** cache repeated prompt prefixes, not a general document database. OpenAI describes saving an eligible prefix and reusing the longest exact matching prefix in later requests. Anthropic exposes cache creation/read token counts for its cacheable prefixes. This can reduce repeated input processing/cost when a stable prompt or document context recurs; changing the prefix may prevent reuse. [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching), [Anthropic prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

Claude's published PDF flow extracts each page's text **and** converts each page to an image, then supplies both to the model so it can interpret charts and layout. Anthropic recommends Files API references for large PDFs or PDFs used repeatedly. This still differs from a vector retrieval index. [Claude PDF support](https://platform.claude.com/docs/en/build-with-claude/pdf-support)

These are documented API behaviors, not a claim that the consumer ChatGPT and Claude apps use exactly the same pipeline for every upload. Their public UI implementation details are not fully specified in these API guides.

**Build implication for hundreds of mixed files:** process files asynchronously and incrementally (hash + parser version), keep source/page/sheet provenance and access metadata, and measure parse/index throughput separately from query latency. At question time, retrieve a small, permission-filtered set of relevant passages/tables. Use prompt caching only for stable repeated prompt/context prefixes, and confirm cache hits from the API usage fields instead of assuming caching explains a fast response. For exact numeric analysis, query typed tables in a database/warehouse; for narrative evidence, use document search. A prompt cache does not make full-corpus analytics reliable.

## Primary documentation consulted

### Agent frameworks

- [Anthropic: Building effective agents](https://www.anthropic.com/research/building-effective-agents)
- [LangGraph multi-agent patterns](https://docs.langchain.com/oss/python/langchain/multi-agent)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview)
- [LlamaIndex workflows](https://developers.llamaindex.ai/python/llamaagents/workflows/)
- [LlamaIndex multi-agent patterns](https://developers.llamaindex.ai/python/framework/understanding/agent/multi_agent/)
- [CrewAI documentation repository](https://github.com/crewAIInc/crewAI/tree/main/docs)
- [OpenAI Agents SDK guide](https://developers.openai.com/api/docs/guides/agents/sdk)
- [Microsoft Agent Framework overview](https://learn.microsoft.com/agent-framework/overview)
- [Google ADK documentation](https://google.github.io/adk-docs/)
- [Haystack introduction](https://docs.haystack.deepset.ai/docs/intro)
- [Pydantic AI overview](https://pydantic.dev/docs/ai/overview/)
- [Spotify data assistant case study](https://engineering.atspotify.com/2026/06/encoding-your-domain-expert-the-context-layer-behind-spotifys-data-assistant)
- [OpenAI in-house data agent](https://openai.com/index/inside-our-in-house-data-agent/)
- [incident.io agentic data analyst](https://incident.io/blog/agentic-data-analyst-pt-i)
- [Uber QueryGPT](https://www.uber.com/us/en/blog/query-gpt/)
- [Kensho/S&P Global Grounding](https://www.langchain.com/blog/customers-kensho)
- [LangChain GTM Deep Agent](https://www.langchain.com/blog/how-we-built-langchains-gtm-agent)

### Data and warehousing

- [Databricks medallion architecture](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)
- [Snowflake Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Snowflake semantic view best practices](https://docs.snowflake.com/en/user-guide/views-semantic/best-practices)
- [BigQuery data agents](https://docs.cloud.google.com/bigquery/docs/create-data-agents)
- [BigQuery conversational analytics](https://docs.cloud.google.com/bigquery/docs/create-conversations/)
- [Databricks Genie Agent quality](https://docs.databricks.com/aws/en/genie-agents/tune-quality/)
- [dbt Semantic Layer](https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl)
- [DuckDB Parquet and query docs](https://duckdb.org/docs/stable/data/parquet/overview)
- [DuckDB FAQ: embedded and persistent modes](https://duckdb.org/faq)
- [ClickHouse: real-time analytics architecture](https://clickhouse.com/ClickHouse)
- [ClickHouse: concurrency sizing](https://clickhouse.com/resources/engineering/high-concurrency-sizing-user-analytics)
- [OpenAI file inputs](https://developers.openai.com/api/docs/guides/file-inputs)
- [OpenAI File Search](https://developers.openai.com/api/docs/guides/tools-file-search)
- [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- [Claude PDF support](https://platform.claude.com/docs/en/build-with-claude/pdf-support)
- [Claude Files API](https://platform.claude.com/docs/en/build-with-claude/files)
- [Claude prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

