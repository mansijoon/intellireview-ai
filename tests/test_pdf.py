from pathlib import Path

from analyzer.pdf_generator import generate_pdf


def test_generate_pdf(tmp_path):
    output = tmp_path / "sample_report.pdf"

    result = generate_pdf(
        str(output),
        85,
        "Executive summary.",
        "No security issues.",
        "No performance issues.",
        "Minor code smells.",
        "This is a sample review report.",
    )

    assert result == str(output)
    assert output.exists()
    assert output.stat().st_size > 0
