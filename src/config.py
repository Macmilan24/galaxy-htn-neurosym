import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://37.27.231.93:7990")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "abc12345")

GALAXY_URL = os.getenv("GALAXY_URL", "https://usegalaxy.org")
GALAXY_API_KEY = os.getenv("GALAXY_API_KEY", "")

PETTA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "PeTTa")
PLN_DIR = os.path.join(PETTA_DIR, "repos", "PLN")
METTA_DOMAIN_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "metta", "domain"
)

TASK_CATEGORIES = [
    "Quality Control",
    "Mapping",
    "Assembly",
    "Variant Calling",
    "RNA Analysis",
    "Annotation",
    "Metagenomic Analysis",
    "Peak Calling",
    "Phylogenetics",
    "Proteomics",
    "Metabolomics",
    "Single-cell",
    "Epigenetics",
    "Imaging",
]

UTILITY_CATEGORIES = [
    "FASTA/FASTQ",
    "SAM/BAM",
    "BED",
    "VCF/BCF",
    "Convert Formats",
    "Text Manipulation",
    "Filter and Sort",
    "Join, Subtract and Group",
    "Collection Operations",
    "Get Data",
    "Send Data",
    "Graph/Display Data",
]
