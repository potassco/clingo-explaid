# How to apply

1. Convert your given unsatisifable input program in the way shown in `example.multi_muc.lp` and `example.multi_muc.converted.lp`
	+ Here every fact that should be an assumption is tranformed in the following way:
	
Original:
```
a.
```

Transformed:
```
{selected(a)}.
a :- selected(a).

#show selected/1.
```

2. Reify this transformed input program
	+ This could be done like this:
	
```bash
clingo test.head_disjunction.converted.lp --output=reify > test.head_disjunction.converted.reified.lp
```

3. Call the reified input program together with the meta encoding for finding Minimal Unsatisifiable Cores
	+ important here are the flags `--heuristic=Domain` and `--enum-mode=domRec` for clingo

```bash
clingo 0 meta_encoding.unsat.lp test.head_disjunction.converted.reified.lp --heuristic=Domain --enum-mode=domRec
```

# TODOs:

+ [ ] Implement/modify a transformer that does the fact transformation
