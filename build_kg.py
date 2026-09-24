"""Chapter 1 → 온톨로지 기반 지식그래프 (Neo4j)
v2: qwen3 thinking 차단(/no_think 프롬프트 스위치) + from_file 적용
"""
import asyncio, time
import neo4j
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.embeddings import OllamaEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.generation.prompts import ERExtractionTemplate

URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "Qwer1234")

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

# ---- 모델 ----
llm = OllamaLLM(
    model_name="qwen3:8b",
    model_params={"options": {"temperature": 0}},
)
embedder = OllamaEmbeddings(model="bge-m3")

# ---- qwen3 thinking 차단: 추출 프롬프트 끝에 /no_think 부착 ----
no_think_template = ERExtractionTemplate(
    template=ERExtractionTemplate.DEFAULT_TEMPLATE + "\n/no_think"
)

driver = neo4j.GraphDatabase.driver(URI, auth=AUTH)

kg_builder = SimpleKGPipeline(
    llm=llm, driver=driver, embedder=embedder,
    schema={"node_types": NODE_TYPES,
            "relationship_types": REL_TYPES,
            "patterns": PATTERNS},
    prompt_template=no_think_template,
    from_file=False, on_error="IGNORE",
)

with open("ch1.txt", encoding="utf-8") as f:
    text = f.read()

t0 = time.time()
asyncio.run(kg_builder.run_async(text=text))
print(f"완료! 소요 시간: {(time.time()-t0)/60:.1f}분")
driver.close()