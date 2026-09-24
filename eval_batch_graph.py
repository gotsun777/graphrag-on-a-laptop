"""평가 배치 v2 — VectorCypherRetriever (그래프 확장 검색)
같은 10문항을 벡터+그래프 검색으로 재실행, eval_results.md에 이어서 기록
"""
import time
import neo4j
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.embeddings import OllamaEmbeddings
from neo4j_graphrag.retrievers import VectorCypherRetriever
from neo4j_graphrag.generation import GraphRAG

URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "Qwer1234")          # ← 교체

RESULT_FILE = "eval_results.md"
RETRIEVER_NAME = "VectorCypherRetriever"

# ---- D세트: 동일 10문항 ----
QUESTIONS = [
    ("T1-1", "What is the maximum penalty under the EU AI Act for prohibited practices?"),
    ("T1-2", "When did Korea's AI Basic Act take effect?"),
    ("T1-3", "What did the FTC order Rite Aid to do regarding facial recognition?"),
    ("T2-4", "Which companies were fined by data protection authorities, and for how much?"),
    ("T2-5", "Who brought the enforcement action against Scatter Lab, and what AI system was involved?"),
    ("T2-6", "Which regulation amended the EU AI Act's compliance calendar, and what did it change?"),
    ("T3-7", "Compare the transparency and labeling obligations for generative AI across the EU, the US, and Korea."),
    ("T3-8", "Which AI systems mentioned in the book were classified as high-risk or high-impact, and under which regulations?"),
    ("T3-9", "List all enforcement actions related to hiring or employment AI, including the regulators involved."),
    ("T3-10", "Which obligations apply to deployers, as opposed to providers, under the EU AI Act?"),
]

# ---- 그래프 확장 쿼리 ----
# 벡터로 찾은 청크(node)에서 → 그 청크에서 추출된 엔티티 → 엔티티의 관계망까지 수집.
# ⚠ FROM_CHUNK는 파이프라인 기본 관계명 — 실행 전 아래 검증 쿼리로 실제 이름 확인 필수:
#    MATCH (c:Chunk)-[r]-(e:__Entity__) RETURN DISTINCT type(r) LIMIT 5;
RETRIEVAL_QUERY = """
WITH node, score
OPTIONAL MATCH (node)-[:FROM_CHUNK]-(e:__Entity__)
OPTIONAL MATCH (e)-[r]-(nb:__Entity__)
WITH node, score,
     collect(DISTINCT e.name + ' [' + head([l IN labels(e) WHERE NOT l STARTS WITH '__']) + ']') AS entities,
     collect(DISTINCT e.name + ' -' + type(r) + '-> ' + nb.name) AS relations
RETURN node.text AS chunk_text, score, entities, relations
"""

def log_result(text):
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

driver = neo4j.GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()
print("Neo4j 연결 확인")

embedder = OllamaEmbeddings(model="bge-m3")
llm = OllamaLLM(model_name="qwen3:8b",
                model_params={"options": {"temperature": 0}})

retriever = VectorCypherRetriever(
    driver,
    index_name="chunk_embeddings",
    embedder=embedder,
    retrieval_query=RETRIEVAL_QUERY,
)
rag = GraphRAG(retriever=retriever, llm=llm)

log_result(f"\n# Evaluation Run — {RETRIEVER_NAME}")
log_result(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

total_t0 = time.time()
for qid, q in QUESTIONS:
    print(f"[{time.strftime('%H:%M:%S')}] {qid} 시작...")
    t0 = time.time()
    try:
        resp = rag.search(query_text=q + " /no_think",
                          retriever_config={"top_k": 5})
        elapsed = time.time() - t0
        log_result(f"## {qid} ({elapsed:.0f}s)")
        log_result(f"**Q:** {q}\n")
        log_result(f"**A:** {resp.answer}\n")
        log_result("**Score (manual):** ☐ correct ☐ partial ☐ wrong — notes:\n")
        log_result("---\n")
        print(f"[{time.strftime('%H:%M:%S')}] {qid} 완료 ({elapsed/60:.1f}분)")
    except Exception as e:
        log_result(f"## {qid} — ERROR\n{e}\n---\n")
        print(f"[{time.strftime('%H:%M:%S')}] {qid} 실패: {e}")

log_result(f"\nTotal: {(time.time()-total_t0)/60:.1f} min")
print(f"\n전체 완료: {(time.time()-total_t0)/60:.1f}분 — 결과: {RESULT_FILE}")
driver.close()