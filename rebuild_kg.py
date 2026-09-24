"""재구축 배치 v3 — 스냅샷 기록 → DB 초기화 → 정제 텍스트 5개 장 인덱싱
사전 조건: clean_extract.py 실행 + 눈 검수 완료된 clean_ch*.txt 5개
"""
import asyncio, time, traceback
import neo4j
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.embeddings import OllamaEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.generation.prompts import ERExtractionTemplate
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter

URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "Qwer1234")     # ← build_kg.py의 AUTH 줄 복사

CHAPTER_FILES = ["clean_ch1.txt", "clean_ch4.txt", "clean_ch7.txt",
                 "clean_ch8.txt", "clean_ch9.txt"]

# ---- Ontology v0.2 ----
NODE_TYPES = ["Regulation", "Organization", "EnforcementAction", "Obligation",
              "RiskCategory", "AISystem", "Role", "Jurisdiction"]
REL_TYPES = ["ISSUED_BY", "APPLIES_IN", "IMPOSES", "APPLIES_TO", "DEFINES",
             "CLASSIFIED_AS", "BROUGHT_BY", "TARGETS", "CONCERNS", "AMENDS"]
PATTERNS = [
    ("Regulation", "ISSUED_BY", "Organization"),
    ("Regulation", "APPLIES_IN", "Jurisdiction"),
    ("Regulation", "IMPOSES", "Obligation"),
    ("Obligation", "APPLIES_TO", "Role"),
    ("Obligation", "APPLIES_TO", "AISystem"),
    ("Regulation", "DEFINES", "RiskCategory"),
    ("AISystem", "CLASSIFIED_AS", "RiskCategory"),
    ("EnforcementAction", "BROUGHT_BY", "Organization"),
    ("EnforcementAction", "TARGETS", "Organization"),
    ("EnforcementAction", "CONCERNS", "AISystem"),
    ("Regulation", "AMENDS", "Regulation"),
]

def log(msg):
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open("build_log.txt", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def snapshot_and_wipe(driver):
    """초기화 전 기존 그래프 스냅샷을 로그에 박제, 그 후 전체 삭제"""
    recs, _, _ = driver.execute_query(
        "MATCH (n) RETURN labels(n) AS type, count(*) AS cnt ORDER BY cnt DESC")
    log("--- ROUND 2 그래프 스냅샷 (초기화 직전) ---")
    for r in recs:
        log(f"  {r['type']}: {r['cnt']}")
    recs, _, _ = driver.execute_query(
        "MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS cnt ORDER BY cnt DESC")
    for r in recs:
        log(f"  [{r['rel']}]: {r['cnt']}")
    driver.execute_query("MATCH (n) DETACH DELETE n")
    recs, _, _ = driver.execute_query("MATCH (n) RETURN count(n) AS c")
    log(f"--- DB 초기화 완료 (남은 노드: {recs[0]['c']}) ---")

async def main():
    # 모든 비동기 객체를 단일 이벤트 루프 안에서 생성 (v2 교훈)
    llm = OllamaLLM(model_name="qwen3:8b",
                    model_params={"options": {"temperature": 0}})
    embedder = OllamaEmbeddings(model="bge-m3")
    no_think = ERExtractionTemplate(
        template=ERExtractionTemplate.DEFAULT_TEMPLATE + "\n/no_think")
    splitter = FixedSizeSplitter(chunk_size=1500, chunk_overlap=150)

    driver = neo4j.GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()
    log("Neo4j 연결 확인")

    snapshot_and_wipe(driver)

    log("========== 재구축 v3 시작 (정제 텍스트) ==========")
    for fn in CHAPTER_FILES:
        try:
            with open(fn, encoding="utf-8") as f:
                text = f.read()
            log(f"=== {fn} 시작 ({len(text)}자) ===")
            builder = SimpleKGPipeline(
                llm=llm, driver=driver, embedder=embedder,
                schema={"node_types": NODE_TYPES,
                        "relationship_types": REL_TYPES,
                        "patterns": PATTERNS},
                prompt_template=no_think,
                text_splitter=splitter,
                from_file=False, on_error="IGNORE",
            )
            t0 = time.time()
            await builder.run_async(text=text)
            log(f"=== {fn} 완료: {(time.time()-t0)/60:.1f}분 ===")
        except Exception:
            log(f"!!! {fn} 실패 — 다음으로 계속")
            log(traceback.format_exc()[-500:])
    log("========== 재구축 v3 종료 ==========")
    driver.close()

asyncio.run(main())