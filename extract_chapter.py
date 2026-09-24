"""책 PDF에서 Chapter 1 텍스트 추출"""
import pymupdf  # pip install pymupdf

PDF_PATH = "AI_Governance_Executive_Guide_BOOK.pdf"   # 책 PDF 파일명으로 교체
doc = pymupdf.open(PDF_PATH)

# Chapter 1은 PDF 페이지 9~15 (0-index로 8~14). 실제 페이지에 맞게 조정
text = "\n".join(doc[p].get_text() for p in range(8, 15))
with open("ch1.txt", "w", encoding="utf-8") as f:
    f.write(text)
print(f"추출 완료: {len(text)}자")