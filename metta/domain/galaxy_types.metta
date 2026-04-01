; ============================================
; EDAM-aligned type hierarchy for PLN verification
; PLN Deduction rule chains these Inheritance links
; ============================================

; --- Sequence data formats ---
(Inheritance fastqsanger FASTQ)
(Inheritance fastqillumina FASTQ)
(Inheritance fastqsolexa FASTQ)
(Inheritance fastq_gz FASTQ)
(Inheritance FASTQ SequenceData)
(Inheritance FASTA SequenceData)
(Inheritance fasta_gz FASTA)
(Inheritance SequenceData BioinformaticsData)

; --- Alignment data formats ---
(Inheritance BAM AlignmentData)
(Inheritance SAM AlignmentData)
(Inheritance CRAM AlignmentData)
(Inheritance AlignmentData BioinformaticsData)

; --- Variant data formats ---
(Inheritance VCF VariantData)
(Inheritance BCF VariantData)
(Inheritance VariantData BioinformaticsData)

; --- Genomic interval formats ---
(Inheritance BED GenomicInterval)
(Inheritance GFF GenomicInterval)
(Inheritance GFF3 GFF)
(Inheritance GTF GFF)
(Inheritance GenomicInterval BioinformaticsData)

; --- Annotation formats ---
(Inheritance GFF AnnotationData)
(Inheritance GFF3 AnnotationData)
(Inheritance AnnotationData BioinformaticsData)

; --- Tabular and report formats ---
(Inheritance tabular TabularData)
(Inheritance csv TabularData)
(Inheritance tsv TabularData)
(Inheritance TabularData Data)
(Inheritance html ReportData)
(Inheritance json ReportData)
(Inheritance pdf ReportData)
(Inheritance txt TextData)
(Inheritance ReportData Data)
(Inheritance TextData Data)

; --- Top-level ---
(Inheritance BioinformaticsData Data)

; --- Format aliases (Galaxy uses these) ---
(Inheritance data Data)
(Inheritance auto Data)
(Inheritance input Data)