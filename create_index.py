"""벡터 인덱스 생성 — 1회만 실행"""
import neo4j
from neo4j_graphrag.indexes import create_vector_index

URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "Qwer1234")

driver = neo4j.GraphDatabase.driver(URI, auth=AUTH)

create_vector_index(
    driver,
    name="chunk_embeddings",
    label="Chunk",
    embedding_property="embedding",
    dimensions=1024,        # bge-m3 차원
    similarity_fn="cosine",
)
print("벡터 인덱스 생성 완료: chunk_embeddings")
driver.close()