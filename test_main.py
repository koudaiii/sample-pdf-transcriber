import fitz
import pytest

import main


def make_pdf(path, texts):
    """textsの各要素を1ページのテキストとして持つPDFをpathに作成する。"""
    doc = fitz.open()
    for text in texts:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()


def make_page_image(page, rect):
    """指定したrectを覆う単色画像をpageに挿入する。"""
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 100), False)
    pix.set_rect(pix.irect, (255, 0, 0))
    page.insert_image(rect, pixmap=pix)


def make_scanned_pdf(path):
    """テキストを持たず、ページ全体を覆う画像のみのPDF（スキャンPDF相当）を作成する。"""
    doc = fitz.open()
    page = doc.new_page()
    make_page_image(page, page.rect)
    doc.save(str(path))
    doc.close()


def test_transcriber_prints_single_page_text(tmp_path, capsys):
    pdf_path = tmp_path / "single.pdf"
    make_pdf(pdf_path, ["Hello, PDF transcriber test!"])

    main.transcriber(str(pdf_path))

    captured = capsys.readouterr()
    assert "Hello, PDF transcriber test!" in captured.out


def test_transcriber_prints_multiple_pages_without_separator(tmp_path, capsys):
    pdf_path = tmp_path / "multi.pdf"
    make_pdf(pdf_path, ["First page content.", "Second page content."])

    main.transcriber(str(pdf_path))

    captured = capsys.readouterr()
    # ページ区切り文字（フォームフィード0x0C）を挿入しない仕様であることを確認する。
    assert "\x0c" not in captured.out
    assert "First page content." in captured.out
    assert "Second page content." in captured.out


def test_main_exits_with_error_when_no_argument(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["main.py"])

    with pytest.raises(SystemExit) as exc_info:
        main.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "usage:" in captured.err


def test_main_exits_with_error_when_file_not_found(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["main.py", "/nonexistent/path.pdf"])

    with pytest.raises(SystemExit) as exc_info:
        main.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "file not found" in captured.err


def test_main_prints_pdf_text_for_valid_path(tmp_path, monkeypatch, capsys):
    pdf_path = tmp_path / "valid.pdf"
    make_pdf(pdf_path, ["Valid PDF content."])
    monkeypatch.setattr("sys.argv", ["main.py", str(pdf_path)])

    main.main()

    captured = capsys.readouterr()
    assert "Valid PDF content." in captured.out


def test_is_scanned_page_true_for_full_page_image(tmp_path):
    pdf_path = tmp_path / "scanned.pdf"
    make_scanned_pdf(pdf_path)

    doc = fitz.open(str(pdf_path))
    assert main.is_scanned_page(doc[0]) is True
    doc.close()


def test_is_scanned_page_false_for_text_with_small_stamp_image(tmp_path):
    pdf_path = tmp_path / "digital_with_stamp.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Digital text with a small stamp image.")
    # ページのごく一部だけを覆う印鑑相当の小さな画像を挿入する。
    small_rect = fitz.Rect(page.rect.x1 - 60, page.rect.y1 - 60, page.rect.x1 - 10, page.rect.y1 - 10)
    make_page_image(page, small_rect)
    doc.save(str(pdf_path))
    doc.close()

    doc = fitz.open(str(pdf_path))
    assert main.is_scanned_page(doc[0]) is False
    doc.close()


def test_is_scanned_page_false_for_text_only_page(tmp_path):
    pdf_path = tmp_path / "text_only.pdf"
    make_pdf(pdf_path, ["No images at all."])

    doc = fitz.open(str(pdf_path))
    assert main.is_scanned_page(doc[0]) is False
    doc.close()


def test_transcriber_prints_warning_for_scanned_page(tmp_path, capsys):
    pdf_path = tmp_path / "scanned.pdf"
    make_scanned_pdf(pdf_path)

    main.transcriber(str(pdf_path))

    captured = capsys.readouterr()
    assert "looks like a scanned image" in captured.out
    assert "page 1" in captured.out
