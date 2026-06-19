from analyzer.pdf_generator import generate_pdf

generate_pdf(
"sample_report.pdf",
85,
"No security issues",
"No performance issues",
"Minor code smells",
"This is a sample review report."
)

print("PDF Created")

