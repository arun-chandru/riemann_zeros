"""Reversible scale-100 representation change of accepted PC9QB5C data.

Original certificate by Samuel Lavery and team, Apache-2.0. All original
notices retained. This is source construction; Lean replay is still required.
"""
from pathlib import Path
from hashlib import sha256
from fractions import Fraction as F
from difflib import unified_diff
import ast
import re
import json

HERE=Path(__file__).resolve().parent
INPUT=HERE.parent/'window_merge/Candidate_taylor20_9point.lean'
EXPECTED='4253579322da07f6196c81d3eb2329740669711656b66d3ffd9f1eed6b68265a'
OUT=HERE/'Candidate_taylor20_pc9_slack.lean'
N=85638285
H=F(672168410564118872522651,10**24)
B=F(436674,10**8)
Q0=(H-B)/(1-F(856382,10**8))
Q=(H-B)/(1-F(N,10**10))

def change(s,a,b,n):
    assert s.count(a)==n,(a,s.count(a),n)
    return s.replace(a,b)

def transform_with_report(raw):
    assert sha256(raw).hexdigest()==EXPECTED
    src=raw.decode('utf-8')
    a=src.index('namespace AMW.Cert.PC9QB5C\n')
    b=src.index('end AMW.Cert.PC9QB5C\n',a)+len('end AMW.Cert.PC9QB5C\n')
    inst=src[a:b]
    bs=ast.literal_eval(re.search(r'^def BS : .* := (\[.*\])$',inst,re.M)[1])
    ts=ast.literal_eval(re.search(r'^def TS : .* := (\[.*\])$',inst,re.M)[1])
    sig=int(re.search(r'^def SIG : ℕ := (\d+)$',inst,re.M)[1])
    coeff=set(bs)|{t[2] for t in ts}|{10**8,sig}
    counts={str(v):len(re.findall(r'(?<![\w])'+str(v)+r'(?![\w])',inst)) for v in sorted(coeff)}
    assert all(counts.values())
    grown=re.sub(r'(?<![\w])\d+(?![\w])',lambda m:str(int(m[0])*100) if int(m[0]) in coeff else m[0],inst)
    grown=change(grown,'def cN : ℕ := 856382\n',f'def cN : ℕ := {N}\n',1)
    inverse={str(v*100):str(v) for v in coeff}
    back=change(grown,f'def cN : ℕ := {N}\n','def cN : ℕ := 856382\n',1)
    back=re.sub(r'(?<![\w])\d+(?![\w])',lambda m:inverse.get(m[0],m[0]),back)
    assert back==inst
    new=src[:a]+grown+src[b:]
    replacements=[
      ('((856382 : ℝ) / 100000000) ≤ Fw W9 g',f'(({N} : ℝ) / 10000000000) ≤ Fw W9 g',1),
      ('(0 : ℝ) < 856382 / 100000000',f'(0 : ℝ) < {N} / 10000000000',2),
      ('(1 - (856382 : ℝ) / 100000000)',f'(1 - ({N} : ℝ) / 10000000000)',2),
      (f'{Q0.numerator} / {Q0.denominator}',f'{Q.numerator} / {Q.denominator}',5)]
    for x,y,n in replacements:new=change(new,x,y,n)
    back=new
    for x,y,n in reversed(replacements):back=change(back,y,x,n)
    back=back[:a]+inst+back[a+len(grown):]
    assert back==src
    notice='''/-
Modified by R. Arun Chandru, 2026-10-12: exact certificate-floor refinement.
Copyright (c) 2026 R. Arun Chandru, for this certificate-slack refinement.
SPDX-License-Identifier: Apache-2.0
-/
'''
    # Put modification notice after imports to avoid an obsolete score header.
    ix=new.index('import ChallengeDeps\n')+len('import ChallengeDeps\n')
    new=new[:ix]+notice+new[ix:]
    assert len(new.encode('utf-8'))<2_000_000
    report={'input_sha256':EXPECTED,'output_sha256':sha256(new.encode()).hexdigest(),
      'output_bytes':len(new.encode()),'score':str(Q),'floor':str(F(N,10**10)),
      'H':str(H),'pressure':str(B),'gain_over_Honly':str(Q-Q0),
      'gain_over_attempt021':str(Q-F(166950417639218487,247859045000000000)),
      'scale':100,'coefficient_literal_counts':counts,'inverse_allowlist':'PASS',
      'kernel_status':'NOT YET REPLAYED','downstream_replacements':replacements}
    return new.encode(),report

def transform(raw):return transform_with_report(raw)[0]

def main():
    raw=INPUT.read_bytes(); new,report=transform_with_report(raw)
    OUT.write_bytes(new)
    (HERE/'combined_candidate_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (HERE/'combined_allowlisted.diff').write_text(''.join(unified_diff(raw.decode().splitlines(True),new.decode().splitlines(True),fromfile=INPUT.name,tofile=OUT.name)),encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
