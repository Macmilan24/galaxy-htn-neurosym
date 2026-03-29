import sys

sys.path.insert(0, ".")

from src.knowledge.neo4j_client import Neo4jClient
from src.extraction.method_extractor import MethodExtractor


def main():
    with Neo4jClient() as db:
        extractor = MethodExtractor(db)

        # 1. Find a good workflow to test with (5-10 tool steps)
        print("=== Looking for a good test workflow... ===")
        workflows = extractor.list_all_workflows()
        print(f"Total workflows: {len(workflows)}")

        # Find one with a reasonable number of steps
        candidates = [
            w for w in workflows if w["num_steps"] and 5 <= int(w["num_steps"]) <= 12
        ]
        print(f"Workflows with 5-12 steps: {len(candidates)}")

        if not candidates:
            print("No suitable workflows found!")
            return

        # Pick the first one with a name
        test_wf = next((w for w in candidates if w["name"]), candidates[0])
        print(f"\nSelected: {test_wf['name']}")
        print(f"  Source: {test_wf['source']}")
        print(f"  Steps: {test_wf['num_steps']}")
        print(f"  ID: {test_wf['id']}")

        # 2. Extract it as an HTN method
        print("\n=== Extracting as HTN method... ===")
        method = extractor.extract_method(test_wf["id"])

        print(f"  Workflow: {method.workflow_name}")
        print(f"  Derived task type: {method.task_type}")
        print(f"  Total steps: {len(method.steps)}")
        print(f"  Tool steps: {method.num_tool_steps}")
        print(f"  Data input steps: {len(method.input_steps)}")
        print(f"  Data flow edges: {len(method.edges)}")
        print(f"  Has parallel branches: {method.has_parallel_branches}")

        # 3. Show the tool sequence in topological order
        print(f"\n=== Tool sequence (topological order) ===")
        uid_to_step = {s.step_uid: s for s in method.steps}
        for i, uid in enumerate(method.topological_order):
            step = uid_to_step.get(uid)
            if step:
                if step.is_tool:
                    print(f"  {i}. [TOOL] {step.tool_name}")
                elif step.is_data_input:
                    print(f"  {i}. [INPUT] (user provides data)")
                elif step.is_subworkflow:
                    print(f"  {i}. [SUBWORKFLOW]")

        # 4. Show parallel groups
        print(f"\n=== Parallel execution layers ===")
        for layer_idx, layer in enumerate(method.parallel_groups):
            step_names = []
            for uid in layer:
                step = uid_to_step.get(uid)
                if step:
                    if step.is_tool:
                        step_names.append(step.tool_name)
                    elif step.is_data_input:
                        step_names.append("(input)")
                    else:
                        step_names.append("(subworkflow)")
            print(f"  Layer {layer_idx}: {', '.join(step_names)}")

        # 5. Show data flow edges
        print(f"\n=== Data flow ===")
        for edge in method.edges:
            src = uid_to_step.get(edge.source_step_uid)
            tgt = uid_to_step.get(edge.target_step_uid)
            src_name = src.tool_name or "(input)" if src else "?"
            tgt_name = tgt.tool_name or "(input)" if tgt else "?"
            print(
                f"  {src_name} --[{edge.from_output_name}]--> {tgt_name} [{edge.input_name}]"
            )


if __name__ == "__main__":
    main()
