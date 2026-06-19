from analyzer.secret_detector import (
    detect_secrets
)

code = '''
password = "admin123"

aws = "AKIA1234567890123456"

token = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
'''

print(
    detect_secrets(code)
)
