"""GraphRAG 질의응답 — 벡터 검색 + qwen3:8b 답변 생성"""
import sys, time
import neo4j
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.embeddings import OllamaEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.generation import GraphRAG

URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "Qwer1234")

driver = neo4j.GraphDatabase.driver(URI, auth=AUTH)
embedder = OllamaEmbeddings(model="bge-m3")     # 구축 때와 동일 모델 필수
llm = OllamaLLM(
    model_name="qwen3:8b",
    model_params={"options": {"temperature": 0}},
)

retriever = VectorRetriever(
    driver,
    index_name="chunk_embeddings",
    embedder=embedder,
    return_properties=["text"],
)
rag = GraphRAG(retriever=retriever, llm=llm)

question = sys.argv[1] if len(sys.argv) > 1 else \
    "Which companies were fined by data protection authorities, and how much? /no_think"

print(f"Q: {question}\n")
t0 = time.time()
response = rag.search(query_text=question, retriever_config={"top_k": 5})
print(f"A: {response.answer}")
print(f"\n(응답 시간: {time.time()-t0:.1f}초)")
driver.close()