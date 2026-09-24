"""평가 배치 — D세트 10문항 자동 실행, 결과를 eval_results.md에 기록
예상 소요: 문항당 10~20분 × 10 = 2~3.5시간 (CPU)
"""
import time
import neo4j
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.embeddings import OllamaEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.generation import GraphRAG

URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "Qwer1234")          # ← ask.py의 AUTH 복사

RESULT_FILE = "eval_results.md"
RETRIEVER_NAME = "VectorRetriever"         # 비교 실험 때 이 이름만 바뀝니다

# ---- D세트: Tier 1(사실) / 2(관계) / 3(다단계·비교) ----
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

def log_result(text):
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

driver = neo4j.GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()
print("Neo4j 연결 확인")

embedder = OllamaEmbeddings(model="bge-m3")
llm = OllamaLLM(model_name="qwen3:8b",
                model_params={"options": {"temperature": 0}})
retriever = VectorRetriever(driver, index_name="chunk_embeddings",
                            embedder=embedder, return_properties=["text"])
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