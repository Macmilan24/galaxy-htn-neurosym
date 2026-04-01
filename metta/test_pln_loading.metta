
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
