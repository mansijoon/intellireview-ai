from analyzer.ai.patch_generation import (
    apply_patch,
    generate_patch,
)


def test_generate_replacement_patch():
    source = "x = 1\n"

    patch = generate_patch(
        file_path="test.py",
        source=source,
        original="x = 1",
        replacement="x = 2",
        reason="Correct the assigned value.",
    )

    assert patch.file_path == "test.py"
    assert patch.original == "x = 1"
    assert patch.replacement == "x = 2"

    assert apply_patch(
        source,
        patch,
    ) == "x = 2\n"


def test_generate_deletion_patch():
    source = (
        "def calculate():\n"
        "    unused = 10\n"
        "    return 42\n"
    )

    patch = generate_patch(
        file_path="review.py",
        source=source,
        original="    unused = 10\n",
        replacement="",
        reason="Remove the unused variable.",
    )

    assert apply_patch(
        source,
        patch,
    ) == (
        "def calculate():\n"
        "    return 42\n"
    )


def test_original_must_exist():
    source = "x = 1\n"

    try:
        generate_patch(
            file_path="test.py",
            source=source,
            original="y = 1",
            replacement="y = 2",
            reason="Fix y.",
        )
    except ValueError as exc:
        assert "not found" in str(exc)
    else:
        raise AssertionError(
            "Expected missing patch target to fail."
        )


def test_replacement_must_change_source():
    source = "x = 1\n"

    try:
        generate_patch(
            file_path="test.py",
            source=source,
            original="x = 1",
            replacement="x = 1",
            reason="No-op.",
        )
    except ValueError as exc:
        assert "differ" in str(exc)
    else:
        raise AssertionError(
            "Expected no-op patch to fail."
        )


def test_patch_only_changes_first_matching_occurrence():
    source = (
        "x = 1\n"
        "x = 1\n"
    )

    patch = generate_patch(
        file_path="test.py",
        source=source,
        original="x = 1\n",
        replacement="x = 2\n",
        reason="Update assignment.",
    )

    patched = apply_patch(
        source,
        patch,
    )

    assert patched == (
        "x = 2\n"
        "x = 1\n"
    )


def test_location_aware_patch_changes_only_targeted_line():
    source = (
        "x = 1\n"
        "y = 1\n"
        "x = 1\n"
    )

    patch = generate_patch(
        file_path="test.py",
        source=source,
        original="x = 1\n",
        replacement="x = 2\n",
        reason="Update the targeted assignment.",
        line_start=3,
        line_end=3,
    )

    assert apply_patch(
        source,
        patch,
    ) == (
        "x = 1\n"
        "y = 1\n"
        "x = 2\n"
    )


def test_location_rejects_target_outside_requested_range():
    source = (
        "x = 1\n"
        "y = 1\n"
    )

    try:
        generate_patch(
            file_path="test.py",
            source=source,
            original="x = 1\n",
            replacement="x = 2\n",
            reason="Update assignment.",
            line_start=2,
            line_end=2,
        )
    except ValueError as exc:
        assert "location" in str(exc)
    else:
        raise AssertionError(
            "Expected location mismatch to fail."
        )


def test_location_rejects_ambiguous_target():
    source = (
        "x = 1\n"
        "x = 1\n"
    )

    try:
        generate_patch(
            file_path="test.py",
            source=source,
            original="x = 1\n",
            replacement="x = 2\n",
            reason="Update assignment.",
            line_start=1,
            line_end=2,
        )
    except ValueError as exc:
        assert "multiple times" in str(exc)
    else:
        raise AssertionError(
            "Expected ambiguous target to fail."
        )
