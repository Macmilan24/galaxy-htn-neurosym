import sys

sys.path.insert(0, ".")

from src.knowledge.neo4j_client import Neo4jClient
from src.extraction.operator_extractor import OperatorExtractor
from src.extraction.method_extractor import MethodExtractor
from src.extraction.variable_lifter import VariableLifter
from src.extraction.method_set_builder import MethodSetBuilder
from src.extraction.metta_generator import MeTTaGenerator


def main():
    with Neo4jClient() as db:
        # --- Step 1: Extract operators ---
        print("=== Step 1: Extracting operators... ===")
        op_extractor = OperatorExtractor(db)
        operators = op_extractor.extract_all()
        print(f"  Extracted {len(operators)} operators")

        # --- Step 2: Extract methods and build method sets ---
        print("\n=== Step 2: Extracting methods and building sets... ===")
        method_extractor = MethodExtractor(db)
        lifter = VariableLifter()
        builder = MethodSetBuilder(method_extractor, lifter)

        # Process first 100 for testing (change to None for all 687)
        method_sets, errors = builder.build_all(max_workflows=100)
        print(f"  Built {len(method_sets)} method sets")
        print(f"  Errors: {len(errors)}")

        multi = [ms for ms in method_sets if not ms.is_singleton]
        print(f"  Sets with alternatives (PLN chooses): {len(multi)}")

        # --- Step 3: Generate MeTTa files ---
        print("\n=== Step 3: Generating MeTTa domain files... ===")
        gen = MeTTaGenerator(output_dir="metta/domain")

        gen.generate_tool_atoms(operators)
        gen.generate_method_sets(method_sets)
        gen.generate_type_hierarchy()
        gen.generate_tool_categories(operators)

        print("\n=== Done! ===")
        print("Generated files in metta/domain/:")
        print("  - tool_atoms.metta (tool TruthValues)")
        print("  - method_sets.metta (HTN methods for PLN selection)")
        print("  - galaxy_types.metta (EDAM type hierarchy)")
        print("  - tool_categories.metta (tool category membership)")


if __name__ == "__main__":
    main()
