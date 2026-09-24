"""파이프라인 조건 재현: /no_think 소프트 스위치 검증"""
import requests

r = requests.post("http://localhost:11434/api/chat", json={
    "model": "qwen3:8b",
    "messages": [{"role": "user",
                  "content": "Extract entities from: 'The FTC fined Rite Aid.' "
                             "Return only JSON: {\"entities\":[{\"name\":...,\"type\":...}]} /no_think"}],
    "options": {"temperature": 0},
    "stream": False,
})
content = r.json()["message"]["content"]
print(content)
print("--- thinking 누출:", "<think>" in content)