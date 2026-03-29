from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


class Neo4jClient:
    def __init__(self, uri=None, user=None, password=None):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def query(self, cypher, **params):
        with self.driver.session() as session:
            result = session.run(cypher, params)
            return [record.data() for record in result]

    def query_single(self, cypher, **params):
        results = self.query(cypher, **params)
        return results[0] if results else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
