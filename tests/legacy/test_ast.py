from analyzer.ast_analyzer import (
    analyze_ast
)

code = """
def monster(
    a,b,c,d,e,f,g
):

    for i in range(10):

        if i > 0:

            for j in range(10):

                if j > 0:

                    for k in range(10):

                        if k > 0:

                            print(i,j,k)

    return 0
"""

print(
    analyze_ast(code)
)
