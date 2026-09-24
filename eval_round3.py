"""3차전 — 정제 그래프 위에서 벡터 vs 그래프 v2 연속 실행
쿼리 v2: 온톨로지 관계만 + 상한(엔티티10·관계12) + 청크 원문 우선
예상: 벡터 ~2h + 그래프 ~2h (야간 기준)
"""
import time
import neo4j
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.embeddings import OllamaEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever, VectorCypherRetriever
from neo4j_graphrag.generation import GraphRAG

URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "Qwer1234")   # ← 교체

RESULT_FILE = "eval_results.md"

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

# ---- RETRIEVAL_QUERY v2 — 2라운드 패인 교정 3종 ----
# ① 온톨로지 10개 관계만 (FROM_CHUNK·NEXT_CHUNK 등 배관 관계 배제)
# ② 상한: 엔티티 10개, 관계 12개 (허브 노드의 관계 홍수 차단)
# ③ chunk_text를 먼저 RETURN (모델 주의를 원문에 고정)
RETRIEVAL_QUERY_V2 = """
WITH node, score
OPTIONAL MATCH (node)-[:FROM_CHUNK]-(e:__Entity__)
WITH node, score, collect(DISTINCT e)[..10] AS ents
UNWIND (CASE WHEN size(ents)=0 THEN [null] ELSE ents END) AS e
OPTIONAL MATCH (e)-[r:ISSUED_BY|APPLIES_IN|IMPOSES|APPLIES_TO|DEFINES|
                     CLASSIFIED_AS|BROUGHT_BY|TARGETS|CONCERNS|AMENDS]-(nb:__Entity__)
WITH node, score, ents,
     collect(DISTINCT e.name + ' -' + type(r) + '-> ' + nb.name)[..12] AS rels
RETURN node.text AS chunk_text, score,
       [x IN ents | x.name] AS entities, rels AS relations
"""

def log_result(text):
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def run_eval(rag, run_name):
    log_result(f"\n# Evaluation Run — {run_name}")
    log_result(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    t_all = time.time()
    for qid, q in QUESTIONS:
        print(f"[{time.strftime('%H:%M:%S')}] [{run_name}] {qid} 시작...")
        t0 = time.time()
        try:
            resp = rag.search(query_text=q + " /no_think",
                              retriever_config={"top_k": 5})
            elapsed = time.time() - t0
            log_result(f"## {qid} ({elapsed:.0f}s)")
            log_result(f"**Q:** {q}\n")
            log_result(f"**A:** {resp.answer}\n")
            log_result("**Score (manual):** ☐ correct ☐ partial ☐ wrong — notes:\n---\n")
            print(f"[{time.strftime('%H:%M:%S')}] [{run_name}] {qid} 완료 ({elapsed/60:.1f}분)")
        except Exception as e:
            log_result(f"## {qid} — ERROR\n{e}\n---\n")
            print(f"[{time.strftime('%H:%M:%S')}] [{run_name}] {qid} 실패: {e}")
    total = (time.time() - t_all) / 60
    log_result(f"\nTotal: {total:.1f} min")
    print(f"\n[{run_name}] 전체 완료: {total:.1f}분")

driver = neo4j.GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()
print("Neo4j 연결 확인 — 3차전 시작")

embedder = OllamaEmbeddings(model="bge-m3")
llm = OllamaLLM(model_name="qwen3:8b",
                model_params={"options": {"temperature": 0}})

# 1부: 벡터 (정제 그래프 기준선)
vec = VectorRetriever(driver, index_name="chunk_embeddings",
                      embedder=embedder, return_properties=["text"])
run_eval(GraphRAG(retriever=vec, llm=llm), "VectorRetriever (Round 3, clean graph)")

# 2부: 그래프 v2
graph = VectorCypherRetriever(driver, index_name="chunk_embeddings",
                              embedder=embedder,
                              retrieval_query=RETRIEVAL_QUERY_V2)
run_eval(GraphRAG(retriever=graph, llm=llm), "VectorCypherRetriever v2 (Round 3, clean graph)")

driver.close()
print("\n3차전 종료 — eval_results.md 확인")