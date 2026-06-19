import re


PATTERNS = {

    "Hardcoded Password":
    r'password\s*=\s*["\'][^"\']+["\']',

    "AWS Access Key":
    r'AKIA[0-9A-Z]{16}',

    "GitHub Token":
    r'ghp_[A-Za-z0-9]{36}',

    "Google/Gemini API Key":
    r'AIza[0-9A-Za-z\-_]{35}',

    "JWT Token":
    r'eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+',

    "Private Key":
    r'-----BEGIN PRIVATE KEY-----',

    "OpenAI API Key":
    r'sk-[A-Za-z0-9]{20,}',

    "Bearer Token":
    r'Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*',

    "MongoDB URL":
    r'mongodb(\+srv)?:\/\/[^\s]+',

    "PostgreSQL URL":
    r'postgres(ql)?:\/\/[^\s]+',

    "MySQL URL":
    r'mysql:\/\/[^\s]+',

    "Database URL":
    r'database_url\s*=\s*["\'][^"\']+["\']',

    "Discord Token":
    r'[A-Za-z\d]{24}\.[A-Za-z\d]{6}\.[A-Za-z\d\-_]{27}',

    "Slack Token":
    r'xox[baprs]-[A-Za-z0-9\-]+'
}


def detect_secrets(code):

    findings = []

    for secret_type, pattern in PATTERNS.items():

        matches = re.findall(
            pattern,
            code
        )

        if matches:

            findings.append(
                {
                    "type": secret_type,
                    "severity": "Critical",
                    "count": len(matches)
                }
            )

    return findings
