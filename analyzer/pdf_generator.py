from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)


def _as_text(value):
    """Convert legacy strings and structured review values to PDF-safe text."""
    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        structured = value.get("review", value)

        if isinstance(structured, str):
            return structured

        verdict = getattr(structured, "verdict", None)
        if verdict:
            return verdict

        return str(structured)

    verdict = getattr(value, "verdict", None)
    if verdict:
        return verdict

    return str(value)


def generate_pdf(
    filename,
    score,
    executive_summary,
    security,
    performance,
    smells,
    review
):

    doc = SimpleDocTemplate(
        filename
    )

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "IntelliReview AI Report",
            styles["Title"]
        )
    )

    content.append(
        Spacer(
            1,
            12
        )
    )

    content.append(
        Paragraph(
            "Executive Summary",
            styles["Heading2"]
        )
    )

    content.append(
        Paragraph(
            executive_summary.replace(
                "\n",
                "<br/>"
            ),
            styles["BodyText"]
        )
    )

    content.append(
        Spacer(
            1,
            12
        )
    )

    content.append(
        Paragraph(
            f"Code Quality Score: {score}/100",
            styles["Normal"]
        )
    )

    content.append(
        Spacer(
            1,
            12
        )
    )

    content.append(
        Paragraph(
            "Security Issues",
            styles["Heading2"]
        )
    )

    content.append(
        Paragraph(
            security.replace(
                "\n",
                "<br/>"
            ),
            styles["BodyText"]
        )
    )

    content.append(
        Spacer(
            1,
            12
        )
    )

    content.append(
        Paragraph(
            "Performance Issues",
            styles["Heading2"]
        )
    )

    content.append(
        Paragraph(
            performance.replace(
                "\n",
                "<br/>"
            ),
            styles["BodyText"]
        )
    )

    content.append(
        Spacer(
            1,
            12
        )
    )

    content.append(
        Paragraph(
            "Code Smells",
            styles["Heading2"]
        )
    )

    content.append(
        Paragraph(
            smells.replace(
                "\n",
                "<br/>"
            ),
            styles["BodyText"]
        )
    )

    content.append(
        Spacer(
            1,
            12
        )
    )

    content.append(
        Paragraph(
            "Full Review",
            styles["Heading2"]
        )
    )

    content.append(
        Paragraph(
            _as_text(review).replace(
                "\n",
                "<br/>"
            ),
            styles["BodyText"]
        )
    )

    doc.build(
        content
    )

    return filename
