from analyzer.secret_detector import (
    detect_secrets
)

code = """
openai_key = "sk-123456789012345678901234567890"

gemini_key = "AIza12345678901234567890123456789012345"

discord = "DISCORD_BOT_TOKEN_PLACEHOLDER"

mongo = "mongodb://localhost:27017"

postgres = "postgresql://user:pass@localhost/db"

mysql = "mysql://root:root@localhost/db"

slack = "xoxb-123456-abcdef"


"""

print(
    detect_secrets(
        code
    )
)
