from analyzer.secret_detector import (
    detect_secrets
)

code = """
openai_key = "TEST_OPENAI_KEY"

gemini_key = "TEST_GEMINI_KEY"

token = "Bearer TEST_TOKEN"

mongo = "mongodb://localhost:27017"

postgres = "postgresql://user:pass@localhost/db"

mysql = "mysql://root:root@localhost/db"

slack = "TEST_SLACK_TOKEN"

discord = "TEST_DISCORD_TOKEN"
"""

print(
    detect_secrets(
        code
    )
)
