import sys

sys.path.insert(0, ".")

from src.knowledge.neo4j_client import Neo4jClient
from src.extraction.method_extractor import MethodExtractor
from src.extraction.variable_lifter import VariableLifter
from src.extraction.workflow_abstractor import WorkflowAbstractor


def main():
    with Neo4jClient() as db:
        extractor = MethodExtractor(db)
        lifter = VariableLifter()
        abstractor = WorkflowAbstractor(db)

        # Pick a few interesting workflows to abstract
        print("=== Abstracting workflows to category level ===\n")

        workflows = extractor.list_all_workflows()

        # Find some specific types
        test_ids = []
        for wf in workflows:
            name = (wf["name"] or "").lower()
            if any(kw in name for kw in ["variant", "rna-seq", "assembly", "chip"]):
                test_ids.append(wf)
            if len(test_ids) >= 8:
                break

        # Also add our Proteome Annotation test case
        test_ids.append(
            {"id": "68e460293b54974828fc12cb9d27d185", "name": "Proteome Annotation"}
        )

        for wf_info in test_ids:
            try:
                method = extractor.extract_method(wf_info["id"])
                lifted = lifter.lift(method)
                abstract = abstractor.abstract(lifted)

                print(f"Workflow: {abstract.workflow_name}")
                print(f"  Task type: {abstract.task_type}")
                print(f"  Concrete: {' -> '.join(abstract.concrete_sequence)}")
                print(f"  Abstract: {' -> '.join(abstract.abstract_sequence)}")
                if abstract.uncategorized_tools:
                    print(f"  Uncategorized: {abstract.uncategorized_tools}")
                print()
            except Exception as e:
                print(f"Error on {wf_info['name']}: {e}\n")

        # Show unique abstract patterns
        print("=== Unique decomposition patterns ===\n")
        all_patterns = {}
        for wf in workflows[:100]:
            try:
                method = extractor.extract_method(wf["id"])
                lifted = lifter.lift(method)
                abstract = abstractor.abstract(lifted)
                key = abstract.pattern_key
                if key not in all_patterns:
                    all_patterns[key] = []
                all_patterns[key].append(abstract.workflow_name)
            except:
                pass

        # Show patterns that appear in multiple workflows
        shared = {k: v for k, v in all_patterns.items() if len(v) > 1}
        print(f"Total unique patterns: {len(all_patterns)}")
        print(f"Patterns shared by multiple workflows: {len(shared)}")
        for pattern, names in sorted(
            shared.items(), key=lambda x: len(x[1]), reverse=True
        ):
            print(f"\n  Pattern: {' -> '.join(pattern)}")
            for name in names:
                print(f"    - {name}")


if __name__ == "__main__":
    main()
