from pydantic import BaseModel, Field
from src.extraction.variable_lifter import LiftedMethod


class MethodSet(BaseModel):
    task_type: str = Field(
        description="The compound task these methods achieve (e.g., 'Annotation', 'Variant Calling')"
    )
    methods: list[LiftedMethod] = Field(
        default_factory=list,
        description="Alternative methods, each from a different workflow",
    )

    class Config:
        arbitrary_types_allowed = True

    @property
    def num_alternatives(self):
        return len(self.methods)

    @property
    def is_singleton(self):
        return len(self.methods) <= 1

    @property
    def all_tools_used(self):
        tools = set()
        for method in self.methods:
            for subtask in method.subtasks:
                tools.add(subtask.tool_name)

        return sorted(tools)

    def summary(self):
        """Human-readable summary of this method set."""
        lines = [f"MethodSet: {self.task_type} ({self.num_alternatives} alternatives)"]
        for i, method in enumerate(self.methods):
            tool_seq = " -> ".join(s.tool_name for s in method.subtasks)
            lines.append(f"  [{i}] {method.workflow_name}: {tool_seq}")
        return "\n".join(lines)


class MethodSetBuilder:
    def __init__(self, method_extractor, variable_lifter):
        self.extractor = method_extractor
        self.lifter = variable_lifter

    def build_all(self, max_workflows=None) -> list[MethodSet]:
        # get all workflow id
        all_workflows = self.extractor.list_all_workflows()
        if max_workflows:
            all_workflows = all_workflows[:max_workflows]

        # extract and lift each workflow

        lifted_methods = []
        errors = []

        for wf in all_workflows:
            try:
                method = self.extractor.extract_method(wf["id"])
                lifted = self.lifter.lift(method)
                lifted_methods.append(lifted)
            except Exception as e:
                errors.append({"workflow": wf.get("name", wf["id"]), "error": str(e)})

        # group by task type
        groups = {}
        for lifted in lifted_methods:
            task = lifted.task_type
            if task not in groups:
                groups[task] = []

            groups[task].append(lifted)

        # build methodsets

        method_sets = []
        for task_type, methods in sorted(groups.items()):
            ms = MethodSet(task_type=task_type, methods=methods)
            method_sets.append(ms)

        return method_sets, errors

    def build_for_task(self, task_type: str) -> MethodSet:
        all_sets, _ = self.build_all()
        for ms in all_sets:
            if ms.task_type == task_type:
                return ms

        return MethodSet(task_type=task_type, methods=[])
