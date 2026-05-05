import pypdf

def read_txt(path):
    """txt 파일 읽기 (인코딩 자동 감지)"""
    for encoding in ['utf-8', 'cp949', 'euc-kr']:
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"파일 인코딩을 인식할 수 없습니다: {path}")

def extract_pdf_text(path):
    """PDF에서 텍스트 추출"""
    text = []
    with open(path, 'rb') as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text.append(extracted)
    result = "\n".join(text).strip()
    if not result:
        raise ValueError("PDF에서 텍스트를 추출할 수 없습니다. 스캔본 PDF일 수 있습니다.")
    return result
