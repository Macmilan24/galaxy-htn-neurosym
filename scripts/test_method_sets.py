import sys

sys.path.insert(0, ".")

from src.knowledge.neo4j_client import Neo4jClient
from src.extraction.method_extractor import MethodExtractor
from src.extraction.variable_lifter import VariableLifter
from src.extraction.method_set_builder import MethodSetBuilder


def main():
    with Neo4jClient() as db:
        extractor = MethodExtractor(db)
        lifter = VariableLifter()
        builder = MethodSetBuilder(extractor, lifter)

        # Build from first 100 workflows (faster than all 687 for testing)
        print("=== Building method sets from first 100 workflows... ===")
        method_sets, errors = builder.build_all(max_workflows=100)

        print(f"\nTotal method sets: {len(method_sets)}")
        print(f"Extraction errors: {len(errors)}")
        if errors:
            print(f"  First 3 errors:")
            for e in errors[:3]:
                print(f"    {e['workflow']}: {e['error']}")

        # Show sets with multiple alternatives (these are where PLNmatters)
        print("\n=== Method sets with MULTIPLE alternatives (PLN will choose) ===")
        multi_sets = [ms for ms in method_sets if not ms.is_singleton]
        for ms in sorted(multi_sets, key=lambda x: x.num_alternatives, reverse=True):
            print(f"\n{ms.summary()}")

        # Show singleton sets (no PLN choice needed)
        singletons = [ms for ms in method_sets if ms.is_singleton]
        print(f"\n=== Singleton method sets (no alternatives): {len(singletons)} ===")
        for ms in singletons[:5]:
            print(
                f"  {ms.task_type}: {ms.methods[0].workflow_name if ms.methods else 'empty'}"
            )
        if len(singletons) > 5:
            print(f"  ... and {len(singletons) - 5} more")

        # Stats
        print("\n=== Stats ===")
        total_methods = sum(ms.num_alternatives for ms in method_sets)
        print(f"Total methods across all sets: {total_methods}")
        print(f"Sets with alternatives (PLN chooses): {len(multi_sets)}")
        print(f"Singleton sets (direct execution): {len(singletons)}")
        all_tools = set()
        for ms in method_sets:
            all_tools.update(ms.all_tools_used)
        print(f"Unique tools used across all methods: {len(all_tools)}")


if __name__ == "__main__":
    main()
