"""Pure certificate representation/floor transform, after the Taylor20 transform.

Original PC8R data and proofs are by Samuel Lavery's team, Apache-2.0;
this local adaptation retains all notices. Exact checker slack permits a
slightly higher floor, after scaling the integer representation by 100.
No frozen input is edited. A generated file still needs official verification.
"""
from pathlib import Path
from fractions import Fraction as Q
from hashlib import sha256
import json
import re

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent/'window_gain/Candidate_taylor20.lean'
INPUT_HASH = '9f27d659b6452a4c670ad02c9d6121dbb9df3ab5c4890c0abb1408bf456177f8'
FACTOR = 100
CN_NEW = 80872002
SA_NEW = 10**10
OLD_H = Q(672168410564118872,10**18)
B = Q(406753,10**8)
C_OLD,C_NEW = Q(808720,10**8),Q(CN_NEW,SA_NEW)
Q_OLD,Q_NEW = (OLD_H-B)/(1-C_OLD),(OLD_H-B)/(1-C_NEW)
COEFFICIENTS = {29489,57723,75811,80707,14035391,19809289,19852596,
    46875914,100000000,200000000,29889708,32311531,47562183,
    80147403,106248171,37074992,67688468,65257054,37999815,
    6250000000000000}

def replace_checked(s,a,b,expected):
    assert s.count(a) == expected,(a,s.count(a),expected)
    return s.replace(a,b)

def transform_with_report(raw):
    assert sha256(raw).hexdigest() == INPUT_HASH
    source = raw.decode('utf-8')
    assert '\r' not in source
    body_start = source.index('import ChallengeDeps\n')
    historical,body = source[:body_start],source[body_start:]
    i0 = body.index('namespace AMW.Cert.PC8R\n')
    i1 = body.index('end AMW.Cert.PC8R\n',i0)+len('end AMW.Cert.PC8R\n')
    inst = body[i0:i1]
    counts = {str(n):len(re.findall(r'(?<![\w])'+str(n)+r'(?![\w])',inst)) for n in sorted(COEFFICIENTS)}
    assert all(counts.values()),counts
    def scale(m):
        n = int(m[0])
        return str(n*FACTOR) if n in COEFFICIENTS else m[0]
    inst_new = re.sub(r'(?<![\w])\d+(?![\w])',scale,inst)
    inst_new = replace_checked(inst_new,'def cN : ℕ := 808720\n',f'def cN : ℕ := {CN_NEW}\n',1)
    # Exact inverse verifies this subsection has no accidental edits.
    reverse = {str(n*FACTOR):str(n) for n in COEFFICIENTS}
    inst_reverse = replace_checked(inst_new,f'def cN : ℕ := {CN_NEW}\n','def cN : ℕ := 808720\n',1)
    inst_reverse = re.sub(r'(?<![\w])\d+(?![\w])',lambda m:reverse.get(m[0],m[0]),inst_reverse)
    assert inst_reverse == inst
    body = body[:i0]+inst_new+body[i1:]
    edits = [
      ('((808720 : ℝ) / 100000000) ≤ Fw W8 g',f'(({CN_NEW} : ℝ) / {SA_NEW}) ≤ Fw W8 g',1),
      ('def cFloor : ℝ := 808720 / 100000000',f'def cFloor : ℝ := {CN_NEW} / {SA_NEW}',1),
      (f'{Q_OLD.numerator} / {Q_OLD.denominator}',f'{Q_NEW.numerator} / {Q_NEW.denominator}',4),
    ]
    for a,b,n in edits: body=replace_checked(body,a,b,n)
    # Whole-body reversal: W8, tables, bit streams, source theorems unaffected
    # except the explicit representation/floor/Q edits above.
    back=body
    for a,b,n in reversed(edits): back=replace_checked(back,b,a,n)
    back=back[:i0]+inst+back[i0+len(inst_new):]
    assert back == source[body_start:]
    assert C_NEW > C_OLD and Q_NEW > Q_OLD
    header = f'''/-
R. Arun Chandru
arun.chandru@gmail.com
https://github.com/arun-chandru
https://x.com/arunchandru
https://researchgate.net/profile/R_Chandru

Copyright (c) 2026 R. Arun Chandru, for this certificate-slack refinement.
SPDX-License-Identifier: Apache-2.0

Changes (2026-10-12): scale PC8R's integer weights, pressures, multiplier
unit and denominator by 100, leaving its real functional and packed
certificate unchanged; use the existing leaves' exact positive slack to
raise the certified floor from 808720/10^8 to {CN_NEW}/10^10.
Combined with the following order-20 window enclosure refinement.
Critical-line proportion: {Q_NEW.numerator}/{Q_NEW.denominator}.
Derived from Samuel Lavery's accepted attempt-020 at
josusanmartin/riemann@e072ab396e34fd937224ff3f666d3d7a5db9fb18.
All inherited notices are retained below and describe historical versions.
This source requires full official compilation and both-kernel replay.
-/
'''
    output=(header+historical+body).encode('utf-8')
    report={
      'input_sha256':sha256(raw).hexdigest(),'output_sha256':sha256(output).hexdigest(),
      'output_bytes':len(output),'integer_scale':FACTOR,'scaled_literal_counts':counts,
      'total_scaled_literals':sum(counts.values()),'cN':CN_NEW,'SA':SA_NEW,
      'floor_old':str(C_OLD),'floor_new':str(C_NEW),'window_H':str(OLD_H),
      'pressure_B':str(B),'score':str(Q_NEW),'score_decimal':str(float(Q_NEW)),
      'gain_over_taylor20':str(Q_NEW-Q_OLD),
      'gain_over_leader':str(Q_NEW-Q(167025220139218487,247978200000000000)),
      'whole_body_reversal':'PASS','historical_notices_verbatim':True,
      'kernel_status':'NOT REPLAYED',
    }
    return output,report

def transform(source_bytes):
    """Pure deterministic byte transform; does not access files or the network."""
    return transform_with_report(source_bytes)[0]

def main():
    raw=INPUT.read_bytes()
    output,report=transform_with_report(raw)
    dest=HERE/'Candidate_taylor20_pc8r_slack.lean'
    dest.write_bytes(output)
    (HERE/'combined_candidate_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__ == '__main__': main()
