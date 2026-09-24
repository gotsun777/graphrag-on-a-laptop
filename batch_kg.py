"""배치 인덱싱 v2 — 단일 이벤트 루프 (Event loop closed 버그 수정)
대상: ch4(EU) → ch7(US) → ch9(비교)  ※ ch8은 완료되어 제외
"""
import asyncio, time, traceback
import pymupdf
import neo4j
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.embeddings import OllamaEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.generation.prompts import ERExtractionTemplate
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter

URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "Qwer1234")          # ← build_kg.py의 AUTH 줄 복사
PDF_PATH = "AI_Governance_Executive_Guide_BOOK.pdf"      # ← 실제 책 PDF 파일명

# ch8_korea는 어제 완료 → 제외됨
CHAPTERS = {
    "ch4_eu_ai_act":  (25, 29),
    "ch7_us_states":  (35, 38),
    "ch9_comparison": (42, 45),
}

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

async def main():
    # v2 수정 핵심: 모든 비동기 객체를 '하나의' 이벤트 루프 안에서 생성
    llm = OllamaLLM(model_name="qwen3:8b",
                    model_params={"options": {"temperature": 0}})
    embedder = OllamaEmbeddings(model="bge-m3")
    no_think = ERExtractionTemplate(
        template=ERExtractionTemplate.DEFAULT_TEMPLATE + "\n/no_think")
    splitter = FixedSizeSplitter(chunk_size=1500, chunk_overlap=150)

    driver = neo4j.GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()
    log("Neo4j 연결 확인")
    doc = pymupdf.open(PDF_PATH)

    log("========== 배치 v2 시작 ==========")
    for name, (p0, p1) in CHAPTERS.items():
        try:
            text = "\n".join(doc[p].get_text() for p in range(p0, p1 + 1))
            log(f"=== {name} 시작 ({len(text)}자, PDF p{p0}-{p1}) ===")
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
            await builder.run_async(text=text)   # v2 수정: asyncio.run 반복 금지
            log(f"=== {name} 완료: {(time.time()-t0)/60:.1f}분 ===")
        except Exception:
            log(f"!!! {name} 실패 — 다음 장으로 계속")
            log(traceback.format_exc()[-500:])

    log("========== 배치 v2 종료 ==========")
    driver.close()

asyncio.run(main())