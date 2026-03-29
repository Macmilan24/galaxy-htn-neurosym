import sys

sys.path.insert(0, ".")

from src.knowledge.neo4j_client import Neo4jClient
from src.extraction.operator_extractor import OperatorExtractor


def main():
    with Neo4jClient() as db:
        extractor = OperatorExtractor(db)

        print("=== Tool Categories (compound task vocabulary) ===")
        categories = extractor.get_tool_categories()
        for cat, count in list(categories.items())[:15]:
            print(f" {cat}: {count} tools")

        print("\n=== Extracting all operators... ===")
        operators = extractor.extract_all()
        print(f"  Total operators extracted: {len(operators)}")

        with_data_inputs = [op for op in operators if op.data_inputs]
        with_data_outputs = [op for op in operators if op.data_outputs]
        print(f"  Operators with data inputs: {len(with_data_inputs)}")
        print(f"  Operators with data outputs: {len(with_data_outputs)}")

        print("\n=== Sample operator: fastp ===")
        fastp_ops = [op for op in operators if "fastp" in op.name.lower()]
        if fastp_ops:
            op = fastp_ops[0]
            print(f"  Name: {op.name}")
            print(f"  Full ID: {op.full_id}")
            print(f"  Version: {op.version}")
            print(f"  Safe name: {op.safe_name}")
            print(f"  Categories: {op.categories}")
            print(f"  Data inputs:")
            for p in op.data_inputs:
                print(f"    - {p.name} ({p.data_type})")
            print(f"  All outputs:")
            for e in op.effects:
                print(f"    - {e.name} ({e.format})")
        else:
            print("  (fastp not found, showing first operator instead)")
            op = operators[0]
            print(f"  Name: {op.name}")
            print(f"  Categories: {op.categories}")


if __name__ == "__main__":
    main()
