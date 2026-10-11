"""Pinned source transformation and exact arithmetic for the next enclosure.

No floating-point number is used to construct or certify a bound. The output
requires independent mathematical review and a full Lean/Comparator replay.
"""
from decimal import Decimal, localcontext
from fractions import Fraction as Q
from hashlib import sha256
from math import factorial, isqrt
from pathlib import Path
import json
import re

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "source_cache/attempt020_Solution.lean"
SOURCE_HASH = "704f3b488692e4f990ffefec34b7f9f39a632594cca2bc7e55d35c3e041dce6e"
LEADER = Q(167025220139218487, 247978200000000000)
R = Q(7071067811865475244, 10**19)
PIHI = Q(314159265358979323847, 10**20)
SCALE = 10**18
OLD_C = Q(190061149269609477, 250000000000000000)
OLD_S = Q(162409234769194159, 250000000000000000)
OLD_H = Q(672168410556873948, SCALE)


def describe(q):
    with localcontext() as ctx:
        ctx.prec = 70
        return {"p": str(q.numerator), "q": str(q.denominator),
                "decimal": str(Decimal(q.numerator)/Decimal(q.denominator))}


def literal(q):
    return f"{q.numerator} / {q.denominator}"


def polynomial(var, parity, n):
    terms = []
    for k in range(parity, n, 2):
        term = "1" if k == 0 else var if k == 1 else f"{var}^{k}"
        if k > 1:
            term += f"/{factorial(k)}"
        if terms:
            term = (" - " if ((k-parity)//2) % 2 else " + ") + term
        terms.append(term)
    return "".join(terms)


def replace_checked(text, old, new, expected=None):
    count = text.count(old)
    assert count > 0 and (expected is None or count == expected), (old, count, expected)
    return text.replace(old, new), count


def build(raw, order):
    assert order % 4 == 0 and order >= 16
    text = raw.decode("utf-8")
    coeff_text = text[text.index("def cAMn :"):text.index("def cAM (j :")]
    coeff = {int(k): int(v) for k, v in re.findall(r"\|\s*(\d+)\s*=>\s*(-?\d+)", coeff_text)}
    assert set(coeff) == set(range(13)) and coeff[0] == 10**9
    pam = sum((Q(coeff[k], 10**9)**2 * (Q(1,2)-1/(4*PIHI**2*k*k))
               for k in range(1, 13)), Q(0))
    error = Q(order+1, order*factorial(order))
    cos_exact = sum((Q((-1)**k)*R**(2*k)/factorial(2*k)
                     for k in range(order//2)), Q(0)) + R**order*error
    cos_int = -((-cos_exact.numerator*SCALE)//cos_exact.denominator)
    c = Q(cos_int, SCALE)
    s = Q(isqrt(SCALE**2-cos_int**2), SCALE)
    assert cos_exact <= c < OLD_C and 0 < OLD_S < s and c*c+s*s <= 1
    numeric_h = Q(3,2)-c/(2*R*s)-pam/(2*s*s)
    h_int = numeric_h.numerator*SCALE//numeric_h.denominator
    h = Q(h_int, SCALE)
    floor = Q(808720, 10**8)
    pressure = Q(406753, 10**8)
    bound = (h-pressure)/(1-floor)
    assert OLD_H < h <= numeric_h and LEADER < bound < 1

    # Historical notices are never rewritten. All substitutions below are in
    # the Lean body and have tightly checked occurrence counts.
    start_body = text.index("import ChallengeDeps\n")
    notices, body = text[:start_body], text[start_body:]
    t0 = body.index("theorem taylor12_F (")
    t1 = body.index("theorem sqrt2_half_bounds :", t0)
    taylor = body[t0:t1]
    for parity in (0,1):
        taylor, _ = replace_checked(taylor, polynomial("θ",parity,12), polynomial("θ",parity,order), 5)
    for old,new,expected in [
        ("taylor12_F", f"taylor{order}_F", 1),
        ("|θ|^12", f"|θ|^{order}", 3),
        ("(13/5748019200)", f"({error.numerator}/{error.denominator})", 3),
        ("(n := 12)", f"(n := {order})", 1),
        ("Finset.range 12", f"Finset.range {order}", 1),
    ]:
        taylor, _ = replace_checked(taylor,old,new,expected)
    body = body[:t0]+taylor+body[t1:]
    c0 = body.index("theorem cos_theta0_le :")
    c1 = body.index("theorem sin_theta0_ge :",c0)
    cosine = body[c0:c1]
    cosine, _ = replace_checked(cosine,"taylor12_F",f"taylor{order}_F",1)
    cosine, _ = replace_checked(cosine,polynomial("r",0,12),polynomial("r",0,order),1)
    cosine, _ = replace_checked(cosine,"r ^ 12 * (13/5748019200)",
                               f"r ^ {order} * ({error.numerator}/{error.denominator})",1)
    body = body[:c0]+cosine+body[c1:]
    replacements = [
        (literal(OLD_C),literal(c),5),
        (literal(OLD_S),literal(s),9),
        ("672168410556873948 / 10 ^ 18", f"{h_int} / 10 ^ 18",3),
        ("672168410556873948 / 1000000000000000000",f"{h_int} / 1000000000000000000",6),
        (literal(LEADER),literal(bound),4),
    ]
    counts = {}
    for old,new,expected in replacements:
        body, counts[old] = replace_checked(body,old,new,expected)
    header = f"""/-
R. Arun Chandru
arun.chandru@gmail.com
https://github.com/arun-chandru
https://x.com/arunchandru
https://researchgate.net/profile/R_Chandru

Copyright (c) 2026 R. Arun Chandru, for this higher-order enclosure refinement.
SPDX-License-Identifier: Apache-2.0

Changes (2026-10-12): replace the initial order-twelve exponential Taylor
enclosure by order {order}; propagate its cosine bound through the existing
circle identity and exact window-to-counting argument.
Window floor: {h_int}/10^18.
Critical-line proportion: {bound.numerator}/{bound.denominator}.
Derived from Samuel Lavery's accepted attempt-020 at
josusanmartin/riemann@e072ab396e34fd937224ff3f666d3d7a5db9fb18.
All inherited notices are retained below and describe historical versions.
The window coefficients, PC8R certificate, hypotheses and counting definitions
are unchanged. This is an analytic-enclosure refinement, not a new method.
-/
"""
    candidate = (header+notices+body).encode("utf-8")
    path = HERE / f"Candidate_taylor{order}.lean"
    path.write_bytes(candidate)
    return {"order": order, "path": str(path), "bytes": len(candidate),
            "sha256": sha256(candidate).hexdigest(), "cos": describe(c),
            "sin": describe(s), "cos_exact_upper": describe(cos_exact),
            "circle_slack": describe(1-c*c-s*s),
            "numeric_h": describe(numeric_h), "H": describe(h),
            "score": describe(bound), "gain": describe(bound-LEADER),
            "replacements": counts, "verification": "NOT KERNEL REPLAYED"}


def main():
    raw = SOURCE.read_bytes()
    assert sha256(raw).hexdigest() == SOURCE_HASH
    results = [build(raw, order) for order in (16,20)]
    (HERE/"candidate_audit.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8")
    for result in results:
        print(json.dumps({k:result[k] for k in ("order","bytes","sha256","H","score","gain")}))


if __name__ == "__main__":
    main()
