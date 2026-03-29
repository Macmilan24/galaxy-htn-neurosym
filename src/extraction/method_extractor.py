from dataclasses import dataclass, field
import rustworkx as rx

from src.config import UTILITY_CATEGORIES


@dataclass
class StepNode:
    step_uid: str
    step_id: str
    step_type: str  # "tool" "data_input"
    tool_name: str
    tool_full_id: str
    tool_version: str
    annotation: str

    @property
    def step_index(self):
        try:
            return int(self.step_id)
        except (ValueError, TypeError):
            return 0

    @property
    def is_tool(self):
        return self.step_type == "tool"

    @property
    def is_data_input(self):
        return self.step_type == "data_input"

    @property
    def is_subworkflow(self):
        return self.step_type == "subworkflow"


@dataclass
class DataFlowEdge:
    source_step_uid: str
    target_step_uid: str
    from_output_name: str
    input_name: str


@dataclass
class HTNMethod:
    workflow_id: str
    workflow_name: str
    workflow_repository: str
    category: str
    task_type: str  # from tool categories

    steps: list[StepNode] = field(default_factory=list)
    edges: list[DataFlowEdge] = field(default_factory=list)

    tool_steps: list[StepNode] = field(default_factory=list)
    input_steps: list[StepNode] = field(default_factory=list)

    topological_order: list[str] = field(default_factory=list)
    parallel_groups: list[list[str]] = field(default_factory=list)
    has_parallel_branches: bool = False

    @property
    def num_tool_steps(self):
        return len(self.tool_steps)

    @property
    def tool_sequence(self):
        uid_to_step = {s.step_uid: s for s in self.steps}
        return [
            uid_to_step[uid].tool_name
            for uid in self.topological_order
            if uid in uid_to_step and uid_to_step[uid].is_tool
        ]


class MethodExtractor:
    def __init__(self, neo4j_client):
        self.db = neo4j_client

    def extract_method(self, workflow_id: str) -> HTNMethod:
        metadata_query = """
              MATCH (w:Workflow {workflow_id: $wf_id})
              RETURN w.workflow_name AS name,
                     w.workflow_repository AS repo,
                     w.category AS category,
                     w.number_of_steps AS num_steps
          """
        # get workflow metadata
        meta = self.db.query_single(metadata_query, wf_id=workflow_id)

        if not meta:
            raise ValueError(f"Workflow {workflow_id} not found")

        method = HTNMethod(
            workflow_id=workflow_id,
            workflow_name=meta["name"] or "",
            workflow_repository=meta["repo"] or "",
            category=meta["category"] or "",
            task_type="",
        )

        # get all step with their tools
        step_query = """
              MATCH (w:Workflow {workflow_id: $wf_id})-[:HAS_STEP]->(s:Step)
              OPTIONAL MATCH (s)-[:STEP_USES_TOOL]->(t:Tool)
              RETURN s.step_uid AS step_uid,
                     s.step_id AS step_id,
                     s.type AS step_type,
                     s.annotation AS annotation,
                     t.name AS tool_name,
                     t.id AS tool_full_id,
                     t.version AS tool_version
          """

        step_records = self.db.query(step_query, wf_id=workflow_id)

        for rec in step_records:
            step = StepNode(
                step_uid=rec["step_uid"] or "",
                step_id=rec["step_id"] or "0",
                step_type=rec["step_type"] or "tool",
                tool_name=rec["tool_name"] or "",
                tool_full_id=rec["tool_full_id"] or "",
                tool_version=rec["tool_version"] or "",
                annotation=rec["annotation"] or "",
            )
            method.steps.append(step)

        step_edge_query = """
              MATCH (w:Workflow {workflow_id:
  $wf_id})-[:HAS_STEP]->(s1:Step)
              MATCH (s1)-[f:STEP_FEEDS_INTO]->(s2:Step)
              RETURN s1.step_uid AS source,
                     s2.step_uid AS target,
                     f.from_output_name AS from_output,
                     f.input_name AS input_name
          """
        edge_records = self.db.query(step_edge_query, wf_id=workflow_id)

        for rec in edge_records:
            edge = DataFlowEdge(
                source_step_uid=rec["source"],
                target_step_uid=rec["target"],
                from_output_name=rec["from_output"] or "",
                input_name=rec["input_name"] or "",
            )
            method.edges.append(edge)

        self._analyze_dag(method)

        method.task_type = self._derive_task_type(method)

        return method

    def _analyze_dag(self, method: HTNMethod):
        method.tool_steps = [s for s in method.steps if s.is_tool]
        method.input_steps = [s for s in method.steps if s.is_data_input]

        # build rx DiGraph
        graph = rx.PyDiGraph()

        uid_to_idx = {}
        for step in method.steps:
            idx = graph.add_node(step.step_uid)
            uid_to_idx[step.step_uid] = idx

        for edge in method.edges:
            src = uid_to_idx.get(edge.source_step_uid)
            tgt = uid_to_idx.get(edge.target_step_uid)
            if src is not None and tgt is not None:
                graph.add_edge(src, tgt, edge)

        # topolgical sort
        try:
            sorted_indices = rx.topological_sort(graph)
            method.topological_order = [graph[idx] for idx in sorted_indices]
        except rx.DAGHasCycle:
            method.topological_order = sorted(
                [s.step_uid for s in method.steps],
                key=lambda uid: next(
                    (s.step_index for s in method.steps if s.step_uid == uid), 0
                ),
            )

        # detect parallel branches
        has_fork = any(
            graph.out_degree(uid_to_idx[s.step_uid]) > 1
            for s in method.steps
            if s.step_uid in uid_to_idx
        )
        has_join = any(
            graph.in_degree(uid_to_idx[s.step_uid]) > 1
            for s in method.steps
            if s.step_uid in uid_to_idx
        )
        method.has_parallel_branches = has_fork or has_join

        # compute parallel groups
        method.parallel_groups = self._compute_layers(graph, uid_to_idx, method.steps)

    def _compute_layers(self, graph, uid_to_idx, steps):

        if not steps:
            return []

        in_degrees = {}
        for step in steps:
            idx = uid_to_idx.get(step.step_uid)
            if idx is not None:
                in_degrees[step.step_uid] = graph.in_degree(idx)

        layers = []
        remaining = dict(in_degrees)

        while remaining:
            current_layer = [uid for uid, deg in remaining.items() if deg == 0]
            if not current_layer:
                current_layer = list(remaining.keys())

            layers.append(current_layer)

            for uid in current_layer:
                del remaining[uid]
                idx = uid_to_idx.get(uid)
                if idx is not None:
                    for successor_idx in graph.successor_indices(idx):
                        succ_uid = graph[successor_idx]
                        if succ_uid in remaining:
                            remaining[succ_uid] -= 1

        return layers

    def _derive_task_type(self, method: HTNMethod) -> str:
        task_from_tools = self._task_type_from_tools(method)
        if task_from_tools != "unknown":
            return task_from_tools

        # Strategy 2: workflow name
        return self._task_type_from_name(method)

    def _task_type_from_tools(self, method: HTNMethod) -> str:
        """Derive task type from tool categories via HAS_TOOL edges."""
        tool_names = [s.tool_name for s in method.tool_steps if s.tool_name]
        if not tool_names:
            return "unknown"

        records = self.db.query(
            """
            MATCH (c:Category)-[:HAS_TOOL]->(t:Tool)
            WHERE t.name IN $tool_names
            RETURN c.name AS category, count(DISTINCT t) AS count
            ORDER BY count DESC
        """,
            tool_names=tool_names,
        )

        task_categories = [
            r
            for r in records
            if r["category"] not in UTILITY_CATEGORIES and r["category"] != ""
        ]

        if task_categories:
            return task_categories[0]["category"]
        return "unknown"

    def _task_type_from_name(self, method: HTNMethod) -> str:

        name = (method.workflow_name or "").lower()

        # Map keywords to task types
        keyword_map = {
            "rna-seq": "RNA Analysis",
            "rnaseq": "RNA Analysis",
            "rna seq": "RNA Analysis",
            "transcriptom": "RNA Analysis",
            "differential expression": "RNA Analysis",
            "variant call": "Variant Calling",
            "variant analysis": "Variant Calling",
            "snp": "Variant Calling",
            "mutation": "Variant Calling",
            "assembl": "Assembly",
            "genome assembly": "Assembly",
            "proteom": "Proteomics",
            "protein": "Proteomics",
            "mass spec": "Proteomics",
            "metagenom": "Metagenomic Analysis",
            "16s": "Metagenomic Analysis",
            "amplicon": "Metagenomic Analysis",
            "microbiome": "Metagenomic Analysis",
            "chip-seq": "Peak Calling",
            "chipseq": "Peak Calling",
            "atac-seq": "Peak Calling",
            "peak call": "Peak Calling",
            "single-cell": "Single-cell",
            "single cell": "Single-cell",
            "scrna": "Single-cell",
            "scrnaseq": "Single-cell",
            "annota": "Annotation",
            "phylogen": "Phylogenetics",
            "metabolom": "Metabolomics",
            "quality control": "Quality Control",
            "qc": "Quality Control",
            "pre-processing": "Quality Control",
            "preprocessing": "Quality Control",
            "trimming": "Quality Control",
            "mapping": "Mapping",
            "alignment": "Mapping",
            "read map": "Mapping",
            "imaging": "Imaging",
            "epigenet": "Epigenetics",
            "methylat": "Epigenetics",
            "bisulfite": "Epigenetics",
            "hi-c": "HiCExplorer",
            "hic": "HiCExplorer",
            "nanopore": "Nanopore",
            "long read": "Nanopore",
            "climat": "Climate Analysis",
            "covid": "Virology",
            "sars": "Virology",
            "virus": "Virology",
            "virol": "Virology",
        }

        for keyword, task_type in keyword_map.items():
            if keyword in name:
                return task_type

        # If nothing matched, use the workflow name itself as the tasktype
        return method.workflow_name or "unknown"

    def list_all_workflows(self) -> list[dict]:
        return self.db.query(
            """
            MATCH (w:Workflow)
            RETURN w.workflow_id AS id,
                    w.workflow_name AS name,
                    w.workflow_repository AS repo,
                    w.category AS source,
                    w.number_of_steps AS num_steps
            ORDER BY w.workflow_name
        """
        )

    def extract_all_for_source(self, source_category: str) -> list[HTNMethod]:

        workflow_ids = self.db.query(
            """
            MATCH (w:Workflow {category: $cat})
            RETURN w.workflow_id AS id
        """,
            cat=source_category,
        )
        return [self.extract_method(r["id"]) for r in workflow_ids]
