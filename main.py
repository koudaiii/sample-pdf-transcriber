import sys
from pathlib import Path

import fitz


def transcriber(path):
    # PDFを開き、各ページのテキストをページ区切りなしで標準出力に出す。
    # ファイル出力(output.txt)は行わない仕様。
    doc = fitz.open(path)  # ドキュメントを開く
    for page in doc:  # ドキュメントのページを反復処理する
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
