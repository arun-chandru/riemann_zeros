"""Bounded reversible transplant; transform(bytes, bytes) has no I/O side effects."""
from fractions import Fraction as F
from hashlib import sha256

BASE_SHA = '9e87ab45039872d4969acdbb5d75076de01d0626de299aaf1b615425dc164639'
LI_SHA = '11520f8af2d31186fc1b2b0304f2e72de29ec90e397b4f36d5792c4ec5190b48'
NEW_N = 6721684105641188747759454444013516755656
NEW_H = F(NEW_N, 10**40)
BASE_Q = F(21541989373036092662021, 31981806507980000000000)
NEW_Q = (NEW_H - F(436674,10**8)) / (1-F(856399825262,10**14))

def block(s, a, b):
    i = s.index(a)
    return s[i:s.index(b,i)+len(b)]

def transform(raw_attempt022: bytes, raw_li: bytes) -> bytes:
    """Change only the admitted window block, propagated literals, and notice."""
    assert sha256(raw_attempt022).hexdigest() == BASE_SHA
    assert sha256(raw_li).hexdigest() == LI_SHA
    base = raw_attempt022.decode('utf-8')
    li = raw_li.decode('utf-8')
    assert '\r' not in base and '\r' not in li
    old_h = '672168410564118872522651 / 1000000000000000000000000'
    old_hp = '672168410564118872522651 / 10 ^ 24'
    old_q = '21541989373036092662021 / 31981806507980000000000'
    new_h = str(NEW_N) + ' / ' + str(10**40)
    new_hp = str(NEW_N) + ' / 10 ^ 40'
    new_q = f'{NEW_Q.numerator} / {NEW_Q.denominator}'
    assert NEW_Q > BASE_Q

    start = base.index('theorem taylor20_F (')
    stop = base.index('theorem aInf_eq :', start)
    old_block = base[start:stop]
    li_start = li.index('theorem taylor20_F (',li.index('namespace ProportionSharpWindow\n'))
    li_stop = li.index('end ProportionSharpWindow',li_start)
    sharp_block = li[li_start:li_stop].rstrip()+'\n'
    assert sharp_block.count('672168410564118874775945444401 / 10 ^ 30') == 2
    new_block = sharp_block.replace('672168410564118874775945444401 / 10 ^ 30',new_hp)

    obsolete_prefix = base[:base.index('-/')+3]
    assert 'Copyright (c) 2026 R. Arun Chandru' in obsolete_prefix
    assert 'Critical-line proportion: 167031227639218487/247987190000000000.' in obsolete_prefix
    notice = '''/-
Modified by R. Arun Chandru, 2026-10-14. Apache-2.0.
Derived from Samuel Lavery's attempt-022 at public source commit
72e3123e7bf235a697dd97d976738afdefdcf257. Refined the rational window enclosure
using Li Xiang's lixiang90-nine-point-refinement, source commit
aa868dc8e4c46e7dda5ac21c47e1c53e1a122b91 (copyright (c) 2026 Li Xiang,
Apache-2.0), based on R. Arun Chandru and Yuhang Shi's order-20 proof.
Original third-party notices below describe their historical source versions.
-/
'''

    assert base.count(old_h) == 16
    assert base.count(old_hp) == 3
    assert base.count(old_q) == 5
    candidate = base[:start]+new_block+base[stop:]
    assert candidate.count(old_hp) == 1
    candidate = candidate.replace(old_h,new_h).replace(old_hp,new_hp).replace(old_q,new_q)
    assert candidate.startswith(obsolete_prefix)
    candidate = notice+candidate.removeprefix(obsolete_prefix)
    assert candidate.count(new_h) == 16
    assert candidate.count(new_hp) == 3
    assert candidate.count(new_q) == 5

    # Invert exactly the admitted proof block, literals, and attribution header.
    restored = obsolete_prefix+candidate.removeprefix(notice)
    assert restored.count(new_block) == 1
    restored = restored.replace(new_block,old_block,1)
    restored = restored.replace(new_h,old_h).replace(new_hp,old_hp).replace(new_q,old_q)
    assert restored.encode('utf-8') == raw_attempt022
    assert block(base,'namespace AMW.Cert.PC9QB6M\n','end RiemannFail\n') == block(candidate,'namespace AMW.Cert.PC9QB6M\n','end RiemannFail\n')
    assert block(base,'import ChallengeDeps','namespace AMW') == block(candidate,'import ChallengeDeps','namespace AMW')
    assert not any(x in new_block for x in ('sorry','admit','axiom','native_decide'))
    return candidate.encode('utf-8')

def main():
    from pathlib import Path
    import difflib
    import json
    here = Path(__file__).resolve().parent
    root = here.parent
    base_path = root / 'sources/attempt-022/proof/Solution.lean'
    li_path = root / 'sources/lixiang90-nine-point-refinement/proof/Solution.lean'
    out = here / 'Candidate_attempt022_sharp40.lean'
    raw_base, raw_li = base_path.read_bytes(), li_path.read_bytes()
    result = transform(raw_base,raw_li)
    out.write_bytes(result)
    (here/'window_only_allowlisted.diff').write_text(''.join(difflib.unified_diff(raw_base.decode().splitlines(True),result.decode().splitlines(True),fromfile=str(base_path.relative_to(root)),tofile=str(out.relative_to(root)))),encoding='utf-8',newline='\n')
    report = {
        'candidate':str(out),
        'candidate_sha256':sha256(result).hexdigest(),
        'base_sha256':BASE_SHA,
        'li_source_sha256':LI_SHA,
        'inverse_allowlist_exact':True,
        'certificate_byte_identical':True,
        'imports_and_options_before_AMW_byte_identical':True,
        'window_floor':str(NEW_H),
        'score':str(NEW_Q),
        'gain_over_attempt022':str(NEW_Q-BASE_Q),
        'changed_blocks':'Taylor20-to-aInf_eq window enclosure; sixteen expanded H literals; three power H literals including two within changed block; five score literals; attribution prefix replaces obsolete author-owned initial comment.',
        'kernel_replay':'Not run by this builder.'
    }
    (here/'window_candidate_manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__ == '__main__':
    main()
