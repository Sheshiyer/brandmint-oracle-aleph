# 🚨 Someone just built a tool that turns any GitHub repo into an interactive kn...

**Source:** https://x.com/ihtesham2005/status/2026264341419528643
**Author:** @ihtesham2005 (ihtesham2005)
**Likes:** 3285 | **RTs:** 444
**Tags:** workflow
**Synced:** 2026-03-02

## Prompt

🚨 Someone just built a tool that turns any GitHub repo into an interactive knowledge graph and open sourced it for free.

It's called GitNexus. Think of it as a visual X-ray of your codebase but with an AI agent you can actually talk to.

Here's what it does inside your browser:

→ Parses your entire GitHub repo or ZIP file in seconds
→ Builds a live interactive knowledge graph with D3.js
→ Maps every function, class, import, and call relationship
→ Runs a 4-pass AST pipeline: structure → parsing → imports → call graph
→ Stores everything in an embedded KuzuDB graph database
→ Lets you query your codebase in plain English with an AI agent

Here's the wildest part:

It uses Web Workers to parallelize parsing across threads so a massive monorepo doesn't freeze your tab.

The Graph RAG agent traverses real graph relationships using Cypher queries not embeddings, not vector search. Actual graph logic.

Ask it things like "What functions call this module?" or "Find all classes that inherit from X" and it traces the answer through the graph.

This is the kind of code intelligence tool enterprise teams pay thousands per month for.

It runs entirely in your browser. Zero server. Zero cost.

Works with TypeScript, JavaScript, and Python.

100% Open Source. MIT License.
