from analyzer.code_metrics import calculate_metrics

sample = """
import os

class Test:
    pass

def hello():
    pass

for i in range(10):
    pass

if True:
    pass
"""

metrics = calculate_metrics(
    sample
)

print(metrics)
