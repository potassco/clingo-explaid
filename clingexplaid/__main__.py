from clingexplaid.utils.transformer import RuleIDTransformer, SignatureToAssumptionTransformer


prg = """
cat(1).
cat(2).
{dog(1..10)}.
mantis(1). mantis(2).
axolotl(X) :- X=1..5. 

something_true.
bike(1); snake(1) :- something_true.
"""


rt = RuleIDTransformer()
res = rt.get_transformer_result(prg)
print(res.output_string)
print(res.output_assumptions)

print("-" * 50)

at = SignatureToAssumptionTransformer(
    program_string=prg,
    signatures=[
        ('cat', 1),
        ('dog', 1),
        ('mantis', 1),
        ('axolotl', 1),
        ('something_true', 0),
        ('snake', 1),
    ]
)
res = at.get_transformer_result()
print(res.output_string)
print([str(a) for a, _ in res.output_assumptions])
