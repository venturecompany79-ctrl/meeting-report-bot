"""스캔본/이미지 PDF 압축: 이미지 다운샘플 + JPEG 재인코딩으로 용량 축소.

Notion 무료 플랜의 파일당 5MB 업로드 한도를 넘는 PDF 를 줄일 때 사용.

의존성: pypdf(이미 requirements 에 포함) + Pillow
  pip install Pillow

사용법:
  python scripts/compress_pdf.py <입력.pdf> <출력.pdf> [목표MB] [최대폭px] [품질]
  예) python scripts/compress_pdf.py company.pdf company_small.pdf 5.0
"""
import sys

from pypdf import PdfReader, PdfWriter


def mb(path):
    import os
    return os.path.getsize(path) / 1048576


def compress(src, dst, max_width=1500, quality=50):
    reader = PdfReader(src)
    writer = PdfWriter(clone_from=reader)

    for page in writer.pages:
        for img in page.images:
            try:
                pil = img.image
                # 큰 이미지는 폭 기준으로 축소
                if pil.width > max_width:
                    ratio = max_width / pil.width
                    new_size = (max_width, max(1, int(pil.height * ratio)))
                    pil = pil.resize(new_size)
                if pil.mode in ("RGBA", "P", "LA"):
                    pil = pil.convert("RGB")
                img.replace(pil, quality=quality)
            except Exception as e:  # noqa: BLE001
                print(f"  (이미지 처리 건너뜀: {e})")

    for page in writer.pages:
        try:
            page.compress_content_streams()
        except Exception:  # noqa: BLE001
            pass

    with open(dst, "wb") as f:
        writer.write(f)


def main():
    src = sys.argv[1]
    dst = sys.argv[2]
    target = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0

    print(f"원본: {mb(src):.2f} MB")
    # 목표 미달 시 점점 더 공격적으로 재시도
    for max_w, q in [(1500, 55), (1300, 45), (1100, 38), (900, 32), (750, 28)]:
        compress(src, dst, max_width=max_w, quality=q)
        size = mb(dst)
        print(f"  시도 (폭<= {max_w}px, q{q}) -> {size:.2f} MB")
        if size <= target:
            print(f"✅ 완료: {dst} ({size:.2f} MB)")
            return
    print(f"⚠️ 목표 {target}MB 미달성. 최종 {mb(dst):.2f} MB (추가 분할 권장)")


if __name__ == "__main__":
    main()
