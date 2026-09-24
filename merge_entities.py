"""6-3 엔티티 병합 — 중복 통합 + 오분류 정리 (APOC 필요)
실행 전후 카운트를 build_log.txt에 기록. 소요: 1분 이내
"""
import time
import neo4j

URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "Qwer1234")   # ← 교체

# 병합 그룹: 정본 이름 → 흡수할 이름들
REGULATION_GROUPS = {
    "EU AI Act (Regulation (EU) 2024/1689)": [
        "EU AI Act — Regulation (EU) 2024/1689",
        "Regulation (EU) 2024/1689 (EU AI Act)",
        "EU AI Act", "AI Act", "Act", "AI Act + GDPR",
        "High-risk regime", "Europe's high-risk regime",
    ],
    "Digital Omnibus on AI (Regulation (EU) 2026/1744)": [
        "Digital Omnibus on AI (Regulation (EU) 2026/1744)",
        "Regulation (EU) 2026/1744 (Digital Omnibus on AI)",
        "Digital Omnibus on AI", "Omnibus",
    ],
    "GDPR (Regulation (EU) 2016/679)": [
        "GDPR", "Regulation (EU) 2016/679 (GDPR)",
    ],
    "Korea AI Basic Act (Act No. 20676)": [
        "AI Basic Act", "AI Basic Act + PIPA",
    ],
    "PIPA (Personal Information Protection Act)": [
        "PIPA", "Personal Information Protection Act (PIPA)",
    ],
    "California SB 942": ["SB 942", "California SB 942"],
    "Executive Order: Ensuring a National Policy Framework for AI": [
        "Federal EO",
        "Executive Order: Ensuring a National Policy Framework for Artificial Intelligence",
    ],
}

ORGANIZATION_GROUPS = {
    "US Equal Employment Opportunity Commission (EEOC)": [
        "Equal Employment Opportunity Commission",
        "US Equal Employment Opportunity Commission",
    ],
    "Apple Inc.": ["Apple", "Apple Inc."],
    "Goldman Sachs Bank USA": ["Goldman Sachs", "Goldman Sachs Bank USA"],
    "Scatter Lab Inc.": ["Scatter Lab Inc.", "Scatter Lab"],
    "Personal Information Protection Commission (PIPC)": [
        "Personal Information Protection Commission (Korea)", "PIPC",
    ],
    "US Department of Justice (DOJ)": ["Department of Justice", "DOJ"],
}

# 삭제: 온톨로지 위반 노이즈 (일반명사, 규정 아닌 보고서, 집행건 파편)
DELETE_NAMES = [
    "Organization", "Government",
    "IBM’s Cost of a Data Breach Report 2025",
    "Stanford University’s AI Index",
    "Regulation on Apple Card program",
]

# 재분류: Organization → Regulation
RELABEL_TO_REGULATION = ["Illinois Biometric Information Privacy Act"]

def log(msg):
    line = f"[{time.strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open("build_log.txt", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def counts(driver, label):
    recs, _, _ = driver.execute_query(
        f"MATCH (n:{label}) RETURN count(n) AS c")
    return recs[0]["c"]

def merge_group(driver, label, canonical, names):
    recs, _, _ = driver.execute_query(
        f"""MATCH (n:{label}) WHERE n.name IN $names
            WITH collect(n) AS nodes WHERE size(nodes) > 1
            CALL apoc.refactor.mergeNodes(nodes,
                 {{properties: "discard", mergeRels: true}}) YIELD node
            SET node.name = $canonical
            RETURN size(nodes) AS merged""",
        names=names, canonical=canonical)
    n = recs[0]["merged"] if recs else 0
    if n:
        log(f"  [{label}] {n}개 → '{canonical}'")

driver = neo4j.GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()

log("========== 6-3 엔티티 병합 시작 ==========")
log(f"before: Regulation {counts(driver,'Regulation')}, "
    f"Organization {counts(driver,'Organization')}")

for canon, names in REGULATION_GROUPS.items():
    merge_group(driver, "Regulation", canon, names)
for canon, names in ORGANIZATION_GROUPS.items():
    merge_group(driver, "Organization", canon, names)

# 재분류
recs, _, _ = driver.execute_query(
    """MATCH (n:Organization) WHERE n.name IN $names
       REMOVE n:Organization SET n:Regulation RETURN count(n) AS c""",
    names=RELABEL_TO_REGULATION)
log(f"  재분류 Organization→Regulation: {recs[0]['c']}개")

# 노이즈 삭제
recs, _, _ = driver.execute_query(
    """MATCH (n:__Entity__) WHERE n.name IN $names
       DETACH DELETE n RETURN count(n) AS c""",
    names=DELETE_NAMES)
log(f"  노이즈 삭제: {recs[0]['c']}개")

log(f"after:  Regulation {counts(driver,'Regulation')}, "
    f"Organization {counts(driver,'Organization')}")
log("========== 6-3 완료 ==========")
driver.close()