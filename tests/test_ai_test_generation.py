import ast

from analyzer.ai.test_generation import (
    generate_test,
    generate_test_for_finding,
)


def test_generate_test_for_function_without_arguments():
    source = (
        "def calculate():\n"
        "    return 42\n"
    )

    result = generate_test(
        file_path="review.py",
        source=source,
        target="calculate",
    )

    assert result.file_path == "review.py"
    assert result.target == "calculate"
    assert "def test_calculate_generated" in result.test_code
    assert "calculate()" in result.test_code

    ast.parse(result.test_code)


def test_generate_test_for_function_with_arguments():
    source = (
        "def calculate(a, b):\n"
        "    return a + b\n"
    )

    result = generate_test(
        file_path="review.py",
        source=source,
        target="calculate",
    )

    assert "calculate(None, None)" in result.test_code

    ast.parse(result.test_code)


def test_generate_test_for_finding_resolves_enclosing_function():
    source = (
        "def calculate():\n"
        "    unused = 10\n"
        "    return 42\n"
    )

    result = generate_test_for_finding(
        source=source,
        file_path="review.py",
        line_start=2,
    )

    assert result.target == "calculate"
    assert "test_calculate_generated" in result.test_code


def test_generate_test_for_finding_rejects_non_function_location():
    source = (
        "VALUE = 42\n"
        "\n"
        "def calculate():\n"
        "    return VALUE\n"
    )

    try:
        generate_test_for_finding(
            source=source,
            file_path="review.py",
            line_start=1,
        )
    except ValueError as exc:
        assert "enclosing function" in str(exc)
    else:
        raise AssertionError(
            "Expected non-function finding location to fail."
        )


def test_generate_test_rejects_unknown_target():
    source = (
        "def calculate():\n"
        "    return 42\n"
    )

    try:
        generate_test(
            file_path="review.py",
            source=source,
            target="missing",
        )
    except ValueError as exc:
        assert "not found" in str(exc)
    else:
        raise AssertionError(
            "Expected unknown target to fail."
        )
