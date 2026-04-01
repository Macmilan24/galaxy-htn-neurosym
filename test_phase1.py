# from neo4j import GraphDatabase

# # d = GraphDatabase.driver("bolt://37.27.231.93:7990", auth=("neo4j", "abc12345"))
# # with d.session() as s:
# #     result = s.run(
# #         """
# #         MATCH (c:Category)-[:HAS_TOOL]->(t:Tool)
# #         RETURN c.name AS category, count(DISTINCT t) AS tool_count
# #         ORDER BY tool_count DESC
# #     """
# #     )
# #     for r in result:
# #         print(f'{r["category"]}: {r["tool_count"]} tools')
# # d.close()

# # d = GraphDatabase.driver("bolt://37.27.231.93:7990", auth=("neo4j", "abc12345"))
# # with d.session() as s:
# #     # What input_type values exist and how common are they?
# #     result = s.run(
# #         """
# #         MATCH (ti:ToolInput)
# #         RETURN ti.input_type AS type, count(*) AS count
# #         ORDER BY count DESC
# #     """
# #     )
# #     print("=== ToolInput types ===")
# #     for r in result:
# #         print(f'  {r["type"]}: {r["count"]}')

# #     # What does fastp's actual data input look like?
# #     print()
# #     print("=== fastp inputs (all) ===")
# #     result2 = s.run(
# #         """
# #         MATCH (ti:ToolInput)-[:TOOL_HAS_INPUT]->(t:Tool)
# #         WHERE t.name = "fastp"
# #         RETURN ti.input_name AS name, ti.input_type AS type
# #         ORDER BY ti.input_name
# #         LIMIT 20
# #     """
# #     )
# #     for r in result2:
# #         print(f'  {r["name"]} -> {r["type"]}')
# # d.close()

# from neo4j import GraphDatabase

# d = GraphDatabase.driver("bolt://37.27.231.93:7990", auth=("neo4j", "abc12345"))
# with d.session() as s:
#     # What categories do the tools in this workflow belong to?
#     result = s.run(
#         """
#         MATCH (w:Workflow {workflow_id:
# "68e460293b54974828fc12cb9d27d185"})
#             -[:HAS_STEP]->(s:Step)-[:STEP_USES_TOOL]->(t:Tool)
#         OPTIONAL MATCH (c:Category)-[:HAS_TOOL]->(t)
#         RETURN t.name AS tool, collect(DISTINCT c.name) AS categories
#     """
#     )
#     for r in result:
#         print(f'{r['tool']}: {r["categories"]}')
# d.close()


import sys

sys.path.insert(0, ".")
from src.knowledge.neo4j_client import Neo4jClient
from src.extraction.method_extractor import MethodExtractor

with Neo4jClient() as db:
    extractor = MethodExtractor(db)
    workflows = extractor.list_all_workflows()

    # Derive task types for a sample
    from collections import Counter

    task_types = Counter()

    # Test on first 50 workflows to see the distribution
    for wf in workflows[:50]:
        try:
            method = extractor.extract_method(wf["id"])
            task_types[method.task_type] += 1
        except Exception as e:
            task_types["ERROR"] += 1

    print("=== Task type distribution (first 50 workflows) ===")
    for task, count in task_types.most_common():
        print(f"  {task}: {count} workflows")
