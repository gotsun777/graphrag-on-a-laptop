"""책 PDF → 5개 장 정제 텍스트 추출 (clean_ch*.txt)
클리닝 규칙: 러닝헤드/페이지번호/장식 배너 제거, 공백 정리
"""
import re
import pymupdf

PDF_PATH = "AI_Governance_Executive_Guide_BOOK.pdf"   # ← 실제 파일명

CHAPTERS = {
    "ch1": (8, 14),
    "ch4": (25, 29),
    "ch7": (35, 38),
    "ch8": (38, 41),
    "ch9": (42, 45),
}

# 제거 규칙
RE_PAGENUM   = re.compile(r"^\s*\d{1,3}\s*$")                  # 페이지 번호만 있는 줄
RE_RUNHEAD   = re.compile(r"Dr\.\s*Woongsik\s*Su", re.I)       # 러닝헤드
RE_SPACEDCAP = re.compile(r"^\s*(?:[A-Z]\s+){2,}[A-Z]\s*$")    # "C H A P T E R" 류 장식
RE_DIAMONDS  = re.compile(r"^[\s◆·—-]+$")                      # 장식 기호 줄

def clean(text: str) -> str:
    out = []
    for line in text.splitlines():
        if RE_PAGENUM.match(line):   continue
        if RE_RUNHEAD.search(line):  continue
        if RE_SPACEDCAP.match(line): continue
        if RE_DIAMONDS.match(line):  continue
        out.append(line.rstrip())
    cleaned = "\n".join(out)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)   # 빈 줄 압축
    return cleaned.strip()

doc = pymupdf.open(PDF_PATH)
for name, (p0, p1) in CHAPTERS.items():
    raw = "\n".join(doc[p].get_text() for p in range(p0, p1 + 1))
    cleaned = clean(raw)
    fn = f"clean_{name}.txt"
    with open(fn, "w", encoding="utf-8") as f:
        f.write(cleaned)
    print(f"{fn}: {len(raw)}자 → {len(cleaned)}자 ({100*len(cleaned)//len(raw)}%)")
print("완료 — clean_*.txt 파일들을 열어 눈으로 확인하세요")