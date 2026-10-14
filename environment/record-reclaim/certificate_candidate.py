"""Standalone reversible, allowlisted scale-1e6 PC9QB6M floor refinement.

Input must be attempt-022 plus the independently audited H40 window change.
All certificate trees/tables and generic proof text are retained. This constructs
source; Lean/kernel, Comparator, and nanoda replay remain required.
"""
from pathlib import Path
from fractions import Fraction as F
from hashlib import sha256
from collections import Counter
import ast
import difflib
import json
import re
import sys

SCALE = 10**6
OLD_N, OLD_D = 856399825262, 10**14
NEW_N, NEW_D = 856399825262157078, 10**20
H = F(6721684105641188747759454444013516755656, 10**40)
B = F(436674, 10**8)
OLD_Q = (H - B) / (1 - F(OLD_N, OLD_D))
NEW_Q = (H - B) / (1 - F(NEW_N, NEW_D))
TOKEN = r'(?<![\w])\d+(?![\w])'


def change(text, old, new, count):
    assert text.count(old) == count, (old, text.count(old), count)
    return text.replace(old, new)


def transform(raw, expected_sha256=None):
    digest = sha256(raw).hexdigest()
    if expected_sha256 is not None:
        assert digest == expected_sha256, (digest, expected_sha256)
    src = raw.decode('utf-8')
    start = src.index('namespace AMW.Cert.PC9QB6M\n')
    end = src.index('end AMW.Cert.PC9QB6M\n', start) + len('end AMW.Cert.PC9QB6M\n')
    inst = src[start:end]
    bs = ast.literal_eval(re.search(r'^def BS : .* := (\[.*\])$', inst, re.M)[1])
    ts = ast.literal_eval(re.search(r'^def TS : .* := (\[.*\])$', inst, re.M)[1])
    sa = int(re.search(r'^def SA : ℕ := (\d+)$', inst, re.M)[1])
    sig = int(re.search(r'^def SIG : ℕ := (\d+)$', inst, re.M)[1])
    assert len(bs) == 8 and len(ts) == 34 and sa == OLD_D
    coeff = set(bs) | {t[2] for t in ts} | {sa, sig}
    assert OLD_N not in coeff
    counts = Counter(int(m[0]) for m in re.finditer(TOKEN, inst) if int(m[0]) in coeff)
    assert set(counts) == coeff
    grown = re.sub(TOKEN, lambda m: str(int(m[0]) * SCALE) if int(m[0]) in coeff else m[0], inst)
    grown = change(grown, f'def cN : ℕ := {OLD_N}\n', f'def cN : ℕ := {NEW_N}\n', 1)
    inverse = {str(value * SCALE): str(value) for value in coeff}
    back = change(grown, f'def cN : ℕ := {NEW_N}\n', f'def cN : ℕ := {OLD_N}\n', 1)
    back = re.sub(TOKEN, lambda m: inverse.get(m[0], m[0]), back)
    assert back == inst, 'Certificate inverse transform failed'
    new_bs = ast.literal_eval(re.search(r'^def BS : .* := (\[.*\])$', grown, re.M)[1])
    new_ts = ast.literal_eval(re.search(r'^def TS : .* := (\[.*\])$', grown, re.M)[1])
    new_sa = int(re.search(r'^def SA : ℕ := (\d+)$', grown, re.M)[1])
    assert new_sa == NEW_D
    assert [F(v, sa) for v in bs] == [F(v, new_sa) for v in new_bs]
    assert [(i, j, F(a, sa), k) for i, j, a, k in ts] == [(i, j, F(a, new_sa), k) for i, j, a, k in new_ts]
    # G contains eight pressure coefficients followed by every one of the 36
    # pair weights, including the two zeros not represented in TS.
    def g_coefficients(body):
        gbody = body.split('def G ', 1)[1].split('\ntheorem ', 1)[0]
        return [F(int(v), int(re.search(r'^def SA : ℕ := (\d+)$', body, re.M)[1]))
                for v in re.findall(r'\((\d+) / \(SA:ℝ\)\)', gbody)]
    old_real = g_coefficients(inst)
    new_real = g_coefficients(grown)
    assert len(old_real) == 44 and old_real == new_real, ('G coefficients', len(old_real), len(new_real))
    result = src[:start] + grown + src[end:]
    replacements = [
        (f'(({OLD_N} : ℝ) / {OLD_D}) ≤ Fw W9 g', f'(({NEW_N} : ℝ) / {NEW_D}) ≤ Fw W9 g', 1),
        (f'(0 : ℝ) < {OLD_N} / {OLD_D}', f'(0 : ℝ) < {NEW_N} / {NEW_D}', 2),
        (f'(1 - ({OLD_N} : ℝ) / {OLD_D})', f'(1 - ({NEW_N} : ℝ) / {NEW_D})', 2),
        (f'{OLD_Q.numerator} / {OLD_Q.denominator}', f'{NEW_Q.numerator} / {NEW_Q.denominator}', 5),
    ]
    for old, new, count in replacements:
        result = change(result, old, new, count)
    back = result
    for old, new, count in reversed(replacements):
        back = change(back, new, old, count)
    back = back[:start] + inst + back[start + len(grown):]
    assert back == src, 'Full-source inverse transform failed'
    notice = '''/-
Modified by R. Arun Chandru, 2026-10-14: exact rational certificate refinement.
Copyright (c) 2026 R. Arun Chandru, for this certificate-floor refinement.
SPDX-License-Identifier: Apache-2.0
-/
'''
    ix = result.index('import ChallengeDeps\n') + len('import ChallengeDeps\n')
    result = result[:ix] + notice + result[ix:]
    output = result.encode('utf-8')
    assert len(output) < 2_000_000
    bound = F(17960006063481832416787, 2097152000000000000000000)
    assert F(OLD_N, OLD_D) < F(NEW_N, NEW_D) <= bound
    report = {
        'input_sha256': digest, 'output_sha256': sha256(output).hexdigest(),
        'output_bytes': len(output), 'uniform_integer_scale': SCALE,
        'old_floor': str(F(OLD_N, OLD_D)), 'new_floor': str(F(NEW_N, NEW_D)),
        'exact_same_tree_floor_cap': str(bound), 'remaining_real_floor_slack': str(bound - F(NEW_N, NEW_D)),
        'H': str(H), 'B': str(B), 'old_score': str(OLD_Q), 'score': str(NEW_Q),
        'score_gain_from_floor': str(NEW_Q - OLD_Q),
        'all_44_real_objective_coefficients_unchanged': True,
        'coefficient_literal_counts': {str(k): v for k, v in sorted(counts.items())},
        'inverse_allowlist': 'PASS', 'downstream_replacements': replacements,
        'unchanged_except_allowlist': 'All source bytes invert exactly before adding the modification notice.',
        'kernel_status': 'NOT YET REPLAYED',
    }
    return output, report


if __name__ == '__main__':
    source, target = map(Path, sys.argv[1:3])
    raw = source.read_bytes()
    output, report = transform(raw, sys.argv[3] if len(sys.argv) > 3 else None)
    target.write_bytes(output)
    target.with_suffix('.audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    target.with_suffix('.allowlisted.diff').write_text(''.join(difflib.unified_diff(
        raw.decode().splitlines(True), output.decode().splitlines(True),
        fromfile=str(source), tofile=str(target))), encoding='utf-8')
    print(json.dumps(report, indent=2))
