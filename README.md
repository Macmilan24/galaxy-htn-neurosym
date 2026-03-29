# HTN + PLN + LLM: Neuro-Symbolic Workflow Generation for Galaxy

A neuro-symbolic AI system that automatically generates executable [Galaxy](https://galaxyproject.org/) bioinformatics workflows from natural language requests, combining the deterministic rigor of **Hierarchical Task Network (HTN)** planning with the probabilistic reasoning of **Probabilistic Logic Networks (PLN)** and the semantic understanding of **Large Language Models (LLMs)**.

Built on the [OpenCog Hyperon](https://hyperon.opencog.org/) ecosystem using [MeTTa](https://github.com/trueagi-io/hyperon-experimental) and [PeTTa](https://github.com/trueagi-io/PeTTa).

## The Problem

Bioinformaticians spend significant time manually constructing analysis workflows -- selecting the right tools, ordering them correctly, ensuring data format compatibility, and configuring parameters. While LLMs can generate plausible-sounding pipelines, they hallucinate non-existent tools and produce biologically invalid sequences at unacceptable rates. Research shows LLMs alone achieve **0% correct hierarchical decompositions** on planning benchmarks.

## The Approach

This system constrains the LLM to what it's good at (understanding natural language) and delegates what it's bad at (planning and reasoning) to formal AI systems:

- **LLM** translates vague human requests ("find mutations in my exome data") into formal task names using structured outputs -- hallucination probability for task names is exactly zero
- **HTN Planner** decomposes high-level tasks into concrete tool sequences using methods extracted from a knowledge graph of real human-authored workflows
- **PLN** selects the optimal tools when alternatives exist (BWA-MEM2 vs Bowtie2 vs HISAT2), verifies pipeline validity through ontological reasoning, and continuously learns from execution outcomes
- The output is a fully executable Galaxy workflow (Format 2 YAML) ready to run on any Galaxy server

## Architecture

```
  Natural Language Query
          |
          v
  +-----------------+
  | LLM Parser      |  "Find SNPs in paired-end exome data"
  | (Structured     |         |
  |  Outputs)       |         v
  +-----------------+  [quality_control, read_trimming,
          |             read_alignment, variant_calling]
          v
  +-----------------+
  | HTN Planner     |  Decomposes each task using methods
  | (Methods from   |  extracted from 687 real workflows
  |  Neo4j KG)      |  in the knowledge graph
  +-----------------+
          |
          v
  +-----------------+
  | PLN Reasoning   |  Selects best tools via TruthValues,
  | (MeTTa/PeTTa)   |  verifies pipeline type-safety via
  |                 |  EDAM ontology Inheritance chains
  +-----------------+
          |
          v
  +-----------------+
  | Galaxy Compiler |  Generates executable .gxwf.yml
  | (Format 2 YAML) |  with proper DAG structure
  +-----------------+
          |
          v
  Executable Galaxy Workflow
```

## Knowledge Graph

The system is backed by a Neo4j knowledge graph containing:

- **166,544 nodes** -- Tools, Workflows, Steps, Inputs, Outputs, and their type annotations
- **241,682 relationships** -- Data flow edges, tool-step bindings, category memberships, and similarity links
- **687 curated workflows** from the [Intergalactic Workflow Commission](https://github.com/galaxyproject/iwc), [WorkflowHub](https://workflowhub.eu/), Galaxy Training Network, and other sources
- **15,511 Galaxy tools** with their input/output specifications

## Why PLN

PLN provides mathematically grounded reasoning under uncertainty. Instead of rigid heuristic scores, each tool carries a **TruthValue** (strength, confidence) that is updated through Bayesian evidence revision as the system observes real execution outcomes. PLN's inference rules (Deduction, Revision, Abduction, Induction) enable:

- **Tool selection**: Combining historical success rates, type compatibility, and evidence transferred from similar tools
- **Pipeline verification**: Chaining format compatibility checks through the EDAM ontology type hierarchy
- **Continuous learning**: Tools that fail get deprioritized; tools that succeed get reinforced -- automatically, without manual intervention

Performance is achieved through [PeTTa](https://github.com/trueagi-io/PeTTa) (MeTTa-to-Prolog transpiler, ~500x speedup) with [MORK](https://github.com/trueagi-io/MORK) as a future acceleration path.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Probabilistic reasoning | [PLN](https://github.com/trueagi-io/PLN) on [MeTTa](https://github.com/trueagi-io/hyperon-experimental) / [PeTTa](https://github.com/trueagi-io/PeTTa) |
| Knowledge graph | [Neo4j](https://neo4j.com/) |
| HTN planning | Python (GTPyhop-style forward decomposition) |
| LLM integration | Gemini or other provider with Structured Outputs |
| Workflow platform | [Galaxy](https://galaxyproject.org/) via [BioBlend](https://bioblend.readthedocs.io/) |
| DAG analysis | [rustworkx](https://github.com/Qiskit/rustworkx) |
| Workflow compilation | Galaxy Format 2 via [gxformat2](https://github.com/galaxyproject/gxformat2) |

## Project Status

**Active development -- Proof of Concept phase.**

Currently implementing the HTN method extraction pipeline (Neo4j -> MeTTa domain) and PLN reasoning layer.

## References

- [ChatHTN: Online Learning of HTN Methods for LLM-HTN Planning](https://arxiv.org/abs/2505.11814) (NeuS 2025)
- [CurricuLAMA: Learning HTN Methods from Landmarks](https://arxiv.org/abs/2404.06325) (FLAIRS 2024)
- [A Roadmap for LLMs in Hierarchical Planning](https://arxiv.org/abs/2501.08068) (AAAI Workshop 2025)
- [From Prompt to Pipeline: LLMs for Bioinformatics Workflows](https://arxiv.org/abs/2507.20122) (2025)
- [XGrammar 2: Dynamic Structured Generation for Agentic LLMs](https://arxiv.org/abs/2601.04426) (2026)
- [OpenCog Hyperon](https://arxiv.org/abs/2310.18318)

## License

MIT

---

*Built at [iCog Labs](https://icog-labs.com/) for the [SingularityNET](https://singularitynet.io/) / [Hyperon](https://hyperon.opencog.org/) ecosystem.*
