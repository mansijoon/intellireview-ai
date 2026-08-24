from analyzer.secret_detector import (
    detect_secrets
)

code = '''
password = "admin123"

aws = "AKIA1234567890123456"

token = "ghp_TEST_TOKEN"
'''

print(
    detect_secrets(code)
)
