import sys
from pathlib import Path

import fitz

# スキャン判定の閾値。
# ページ内の画像のbbox面積がページ面積に対してこの割合以上を占める場合、
# 「ページ全体を覆う画像＝スキャン画像として焼き込まれたページ」とみなす。
IMAGE_COVERAGE_THRESHOLD = 0.9


def is_scanned_page(page):
    # スキャンPDF（＝テキストオブジェクトを持たず、ページ全体が1枚の画像として
    # 焼き込まれているページ）かどうかを、画像のページ内占有率のみで判定する。
    # テキスト量では判定しない（記入項目が少ないデジタル帳票を誤判定しないため）。
    page_area = page.rect.width * page.rect.height
    if page_area <= 0:
        return False

    for image in page.get_images(full=True):
        xref = image[0]
        for bbox in page.get_image_rects(xref):
            coverage = (bbox.width * bbox.height) / page_area
            if coverage >= IMAGE_COVERAGE_THRESHOLD:
                return True
    return False


def transcriber(path):
    # PDFを開き、各ページのテキストをページ区切りなしで標準出力に出す。
    # ファイル出力(output.txt)は行わない仕様。
    # デジタルPDF（テキストオブジェクトを持つページ）はテキストをそのまま出力する。
    # スキャンPDF（is_scanned_pageがTrueのページ）はOCR未対応のため、
    # その旨を示すプレースホルダーメッセージを出力する。
    doc = fitz.open(path)  # ドキュメントを開く
    for page in doc:  # ドキュメントのページを反復処理する
        if is_scanned_page(page):
            print(f"[warning: page {page.number + 1} looks like a scanned image; OCR is not supported yet]")
            continue
        text = page.get_text()  # プレーンテキストを取得する
        print(text, end="")  # ページのテキストを標準出力へ書き込む（改行はテキストに含まれる分のみ）
    doc.close()


def main():
    # 使い方: uv run main.py <path-to-pdf>
    # 仕様: 引数なし、またはファイルが存在しない場合はエラーメッセージをstderrへ出し、
    #       終了コード1で終了する。
    if len(sys.argv) != 2:
        print("usage: python main.py <path-to-pdf>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    if not Path(path).is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    transcriber(path)


if __name__ == "__main__":
    main()
