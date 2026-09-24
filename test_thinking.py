"""qwen3:8b의 think=False + JSON format이 실제로 작동하는지 검증"""
import requests, json

r = requests.post("http://localhost:11434/api/chat", json={
    "model": "qwen3:8b",
    "messages": [{"role": "user",
                  "content": "Extract entities from: 'The FTC fined Rite Aid.' "
                             "Return JSON with keys: entities (list of name, type)."}],
    "think": False,
    "format": "json",
    "options": {"temperature": 0},
    "stream": False,
})
content = r.json()["message"]["content"]
print("--- 응답 원문 ---")
print(content)
print("--- 판정 ---")
print("thinking 누출:", "<think>" in content)
try:
    json.loads(content)
    print("JSON 유효: True")
except Exception as e:
    print("JSON 유효: False —", e)