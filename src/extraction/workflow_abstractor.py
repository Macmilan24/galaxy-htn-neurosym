from pydantic import BaseModel, Field


class AbstractStep(BaseModel):
    tool_name: str
    tool_full_id: str
    categories: list[str] = Field(default_factory=list)
    primary_category: str = ""

    @property
    def has_catergory(self):
        return bool(self.primary_category)


class AbstractPipeline(BaseModel):
    workflow_name: str
    task_type: str
    concrete_sequence: list[str] = Field(default_factory=list)
    abstract_sequence: list[str] = Field(default_factory=list)
    steps: list[AbstractStep] = Field(default_factory=list)
    uncategorized_tools: list[str] = Field(default_factory=list)

    @property
    def pattern_key(self):
        return tuple(self.abstract_sequence)


class WorkflowAbstractor:
    def __init__(self, neo4j_client):
        self.db = neo4j_client
        self._tool_category_cache = {}

    def _load_tool_categories(self):
        if self._tool_category_cache:
            return

        records = self.db.query(
            """
              MATCH (c:Category)-[:HAS_TOOL]->(t:Tool)
              RETURN t.name AS tool_name, collect(DISTINCT c.name) AS categories
          """
        )
        for rec in records:
            self._tool_category_cache[rec["tool_name"]] = rec["categories"]

    def _pick_primary_category(self, categories: list[str]) -> str:
        from src.config import UTILITY_CATEGORIES

        task_cats = [c for c in categories if c and c not in UTILITY_CATEGORIES]
        if task_cats:
            # use a manual preferred list
            # TODO: use a data-driven ranking
            preferred = [
                "Quality Control",
                "Mapping",
                "Assembly",
                "Variant Calling",
                "RNA Analysis",
                "Annotation",
                "Peak Calling",
                "Proteomics",
                "Metagenomic Analysis",
                "Single-cell",
                "Phylogenetics",
                "Metabolomics",
                "Epigenetics",
                "Imaging",
                "Nanopore",
            ]

            for pref in preferred:
                if pref in task_cats:
                    return pref

            return task_cats[0]

        util_cats = [c for c in categories if c and c in UTILITY_CATEGORIES]
        if util_cats:
            return util_cats[0]

        return ""

    def abstract(self, lifted_method) -> AbstractPipeline:
        self._load_tool_categories()

        pipeline = AbstractPipeline(
            workflow_name=lifted_method.workflow_name,
            task_type=lifted_method.task_type,
        )

        for subtask in lifted_method.subtasks:
            categories = self._tool_category_cache.get(subtask.tool_name, [])
            primary = self._pick_primary_category(categories)

            step = AbstractStep(
                tool_name=subtask.tool_name,
                tool_full_id=subtask.tool_full_id,
                categories=categories,
                primary_category=primary,
            )

            pipeline.steps.append(step)
            pipeline.concrete_sequence.append(primary)

            if primary:
                pipeline.abstract_sequence.append(primary)
            else:
                pipeline.abstract_sequence.append(f"[{subtask.tool_name}]")
                pipeline.uncategorized_tools.append(subtask.tool_name)

        return pipeline
