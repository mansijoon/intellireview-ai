import analyzer.review_engine as review_engine


def test_review_code_mock():
    original = review_engine.USE_MOCK

    try:
        review_engine.USE_MOCK = True

        result = review_engine.review_code(
            "def add(a, b):\n    return a + b\n"
        )

        assert result
    finally:
        review_engine.USE_MOCK = original
