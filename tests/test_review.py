import analyzer.review_engine as engine


def test_review_code_mock(monkeypatch):
    monkeypatch.setattr(engine, "USE_MOCK", True)

    result = engine.review_code(
        """
password = "admin123"

for i in range(10):
    for j in range(10):
        print(i, j)
"""
    )

    assert result is not None
