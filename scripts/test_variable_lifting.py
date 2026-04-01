import sys

sys.path.insert(0, ".")

from src.knowledge.neo4j_client import Neo4jClient
from src.extraction.method_extractor import MethodExtractor
from src.extraction.variable_lifter import VariableLifter


def main():
    with Neo4jClient() as db:
        extractor = MethodExtractor(db)
        lifter = VariableLifter()

        # Use the same Proteome Annotation workflow we tested before
        workflow_id = "68e460293b54974828fc12cb9d27d185"

        print("=== Extracting workflow... ===")
        method = extractor.extract_method(workflow_id)
        print(f"  Workflow: {method.workflow_name}")
        print(f"  Task type: {method.task_type}")
        print(f"  Tool steps: {method.num_tool_steps}")
        print(f"  Data flow edges: {len(method.edges)}")

        print("\n=== Lifting variables... ===")
        lifted = lifter.lift(method)
        print(f"  Variables created: {lifted.variable_count}")
        print(f"  Required inputs: {len(lifted.required_inputs)}")
        print(f"  Lifted subtasks: {len(lifted.subtasks)}")

        print("\n=== Variable table ===")
        for (step_uid, port), var in lifted.variables.items():
            # Find the step name for readability
            step = next((s for s in method.steps if s.step_uid == step_uid), None)
            step_name = step.tool_name if step and step.is_tool else "(input)"
            consumers = [
                f"{next((s.tool_name for s in method.steps if s.step_uid == c['step_uid']), '?')}[{c['input_port']}]"
                for c in var.consumed_by
            ]
            print(
                f"  {var.name}: {step_name}[{port}] -> {', '.join(consumers) or '(terminal output)'}"
            )

        print("\n=== Workflow-level inputs (user must provide) ===")
        for var in lifted.required_inputs:
            consumers = [
                f"{next((s.tool_name for s in method.steps if s.step_uid == c['step_uid']), '?')}[{c['input_port']}]"
                for c in var.consumed_by
            ]
            print(f"  {var.name} -> feeds: {', '.join(consumers)}")

        print("\n=== Lifted method (abstract template) ===")
        for i, subtask in enumerate(lifted.subtasks):
            print(f"  {i}. {subtask}")

        # Show the before/after comparison
        print("\n=== Before (concrete) vs After (abstract) ===")
        print("  BEFORE: Filter --[kept_lines]--> ID Converter [input|file]")
        # Find the corresponding lifted version
        for subtask in lifted.subtasks:
            if "Filter" in subtask.tool_name:
                print(f"  AFTER:  {subtask}")
                break


if __name__ == "__main__":
    main()
