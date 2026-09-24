"""3자 연결 테스트: Python ↔ Neo4j, Python ↔ Ollama"""
import requests
from neo4j import GraphDatabase

# --- 1. Neo4j 연결 ---
URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "Qwer1234")

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    records, _, _ = driver.execute_query("RETURN 'Neo4j 연결 성공' AS msg")
    print("[1]", records[0]["msg"])

# --- 2. Ollama 서버 확인 ---
r = requests.get("http://localhost:11434/api/tags")
models = [m["name"] for m in r.json()["models"]]
print("[2] Ollama 모델 목록:", models)

# --- 3. 소형 모델로 생성 테스트 ---
r = requests.post("http://localhost:11434/api/generate", json={
    "model": "qwen2.5:1.5b",
    "prompt": "안녕하세요를 영어로 번역하면?",
    "stream": False,
})
print("[3] LLM 응답:", r.json()["response"][:100])

# --- 4. 임베딩 테스트 (bge-m3) ---
r = requests.post("http://localhost:11434/api/embed", json={
    "model": "bge-m3",
    "input": "도서관은 지식의 저장소이다",
})
vec = r.json()["embeddings"][0]
print(f"[4] 임베딩 차원: {len(vec)}, 앞 3개 값: {vec[:3]}")