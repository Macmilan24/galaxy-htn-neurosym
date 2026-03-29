from dataclasses import dataclass, field


@dataclass
class Precondition:
    name: str
    data_type: str  # "data", "text"
    uid: str = ""

    @property
    def is_data_input(self):
        return self.data_type in (
            "data",
            "data_collection",
            "hidden_data",
            "upload_dataset",
            "file",
        )


@dataclass
class Effect:
    name: str
    format: str
    uid: str = ""


@dataclass
class HTNOperator:
    tool_id: str  # hashed id
    full_id: str
    name: str
    description: str
    version: str
    owner: str
    categories: list[str] = field(default_factory=list)
    preconditions: list[Precondition] = field(default_factory=list)
    effects: list[Effect] = field(default_factory=list)

    @property
    def safe_name(self):
        return (
            self.name.replace(" ", "_")
            .replace("/", "_")
            .replace("-", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("+", "plus")
            .replace(".", "_")
        )

    @property
    def data_inputs(self):
        return [p for p in self.preconditions if p.is_data_input]

    @property
    def data_outputs(self):
        return [e for e in self.effects if e.format and e.format != "auto"]

    @property
    def parameter_inputs(self):
        return [p for p in self.preconditions if not p.is_data_input]


class OperatorExtractor:
    def __init__(self, neo4j_client):
        self.db = neo4j_client

    def extract_all(self) -> list[HTNOperator]:

        query = """
              MATCH (t:Tool)
              OPTIONAL MATCH (ti:ToolInput)-[:TOOL_HAS_INPUT]->(t)
              OPTIONAL MATCH (t)-[:TOOL_HAS_OUTPUT]->(to:ToolOutput)
              OPTIONAL MATCH (c:Category)-[:HAS_TOOL]->(t)
              RETURN t.tool_id AS tool_id,
                     t.id AS full_id,
                     t.name AS name,
                     t.description AS description,
                     t.version AS version,
                     t.owner AS owner,
                     collect(DISTINCT ti {
                         .input_name, .input_type, .tool_input_uid
                     }) AS inputs,
                     collect(DISTINCT to {
                         .output_name, .output_format, .tool_output_uid
                     }) AS outputs,
                     collect(DISTINCT c.name) AS categories
          """

        records = self.db.query(query)

        operators = []
        for rec in records:
            op = HTNOperator(
                tool_id=rec["tool_id"] or "",
                full_id=rec["full_id"] or "",
                name=rec["name"] or "unknown",
                description=rec["description"] or "",
                version=rec["version"] or "",
                owner=rec["owner"] or "",
                categories=[c for c in rec["categories"] if c],
                preconditions=[
                    Precondition(
                        name=inp.get("input_name", ""),
                        data_type=inp.get("input_type", ""),
                        uid=inp.get("tool_input_uid", ""),
                    )
                    for inp in rec["inputs"]
                    if inp.get("input_name")  # skip empty entries
                ],
                effects=[
                    Effect(
                        name=out.get("output_name", ""),
                        format=out.get("output_format", ""),
                        uid=out.get("tool_output_uid", ""),
                    )
                    for out in rec["outputs"]
                    if out.get("output_name")  # skip empty entries
                ],
            )

            operators.append(op)
        return operators

    def extract_by_category(self, category_name: str) -> list[HTNOperator]:
        all_ops = self.extract_all()
        return [op for op in all_ops if category_name in op.categories]

    def get_tool_categories(self) -> dict[str, int]:
        query = """
              MATCH (c:Category)-[:HAS_TOOL]->(t:Tool)
              RETURN c.name AS category, count(DISTINCT t) AS count
              ORDER BY count DESC
          """
        records = self.db.query(query)
        return {r["category"]: r["count"] for r in records}
