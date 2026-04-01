import sys
import subprocess

sys.path.insert(0, ".")


def main():
    # Write a small test MeTTa file that imports our domain and queries it
    test_metta = """
; Import PLN library
!(import! &self lib_pln)

; Load our generated domain files
!(import! &self domain/tool_atoms)
!(import! &self domain/method_sets)
!(import! &self domain/galaxy_types)
!(import! &self domain/tool_categories)

; === Test 1: Can we query a tool's TruthValue? ===
!(println! "=== Test 1: Tool TruthValues ===")
!(println! (tool-quality fastp))
!(println! (tool-quality Map_with_BWA_MEM))
!(println! (tool-quality Bowtie2))

; === Test 2: Can we query category membership? ===
!(println! "=== Test 2: Category membership ===")
!(match &self (Member $tool Mapping) (println! $tool))

; === Test 3: Can PLN chain the type hierarchy? ===
!(println! "=== Test 3: Type hierarchy ===")
!(match &self (Inheritance FASTQ $parent) (println! (FASTQ inherits-from
$parent)))
!(match &self (Inheritance BAM $parent) (println! (BAM inherits-from
$parent)))

; === Test 4: Can we see method alternatives for a task? ===
!(println! "=== Test 4: Method alternatives ===")
!(match &self (= (method-for Variant_Calling $method) $body) (println!
(method: $method)))

; === Test 5: What tools does a method use? ===
!(println! "=== Test 5: Tools in a method ===")
!(match &self (MethodUsesTool COVID_19___Genomics__4__PE_Variation $tool)
(println! (uses: $tool)))
"""

    # Write the test file into the metta directory
    test_path = "metta/test_pln_loading.metta"
    with open(test_path, "w") as f:
        f.write(test_metta)
    print(f"Written test file: {test_path}")

    # Run it through PeTTa
    import os

    petta_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "PeTTa"
    )
    print(f"\nRunning through PeTTa from {petta_dir}...")
    print("=" * 60)

    result = subprocess.run(
        ["sh", "run.sh", f"../{test_path}"],
        cwd=petta_dir,
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:500])
    if result.returncode != 0:
        print(f"\nReturn code: {result.returncode}")


if __name__ == "__main__":
    main()
