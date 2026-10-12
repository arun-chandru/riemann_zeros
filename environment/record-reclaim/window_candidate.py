"""Pinned, reversible merge of the accepted nine-point and Taylor20 proofs.

Only exact rational arithmetic constructs or checks constants.  This is a
source transformation and private arithmetic audit, not a Lean verification.
"""

from decimal import Decimal, localcontext
from difflib import unified_diff
from fractions import Fraction as Q
from hashlib import sha256
from math import factorial, isqrt
from pathlib import Path
import json
import re


HERE = Path(__file__).resolve().parent
SOURCES = HERE.parent / "sources"
PINNED = {
    "attempt-021": "01128ffed4efa6544f76c8d33410d945a029647380e1313cc0a19ea3e3749f60",
    "master-of-puppets3": "6ad1bd36031a1d372bf86ac1ed9d7895587768feba5f95a117bed9df217ea6ca",
    "shi-anchor-variance-refinement-2026": "e5862a0bf5b0229eee0357cd41921b7e5174ec3272b960f9a6a6e37e4682da9d",
}
OLD_H = Q(672168410556873948, 10**18)
OLD_SCORE = Q(166950417639218487, 247859045000000000)
NEW_H = Q(672168410564118872522651, 10**24)
B = Q(436674, 10**8)
C_FLOOR = Q(856382, 10**8)
SCORE = (NEW_H - B) / (1 - C_FLOOR)
NOTICE = """/-
Modified by R. Arun Chandru, 2026-10-12: merge the order-20 window enclosure
from master-of-puppets3 and propagate the sharpened rational HW floor.
Terminal HW-floor refinement adapted from Yuhang Shi.
Copyright (c) 2026 Yuhang Shi.
SPDX-License-Identifier: Apache-2.0
-/
"""
OWNED_OLD_HEADER = """/-
R. Arun Chandru
arun.chandru@gmail.com
https://github.com/arun-chandru
https://x.com/arunchandru
https://researchgate.net/profile/R_Chandru

Copyright (c) 2026 R. Arun Chandru, for the circle-enclosure refinement.
SPDX-License-Identifier: Apache-2.0

Critical-line proportion: 167031227639218487/247987190000000000.

-/
"""


def digest(raw):
    return sha256(raw).hexdigest()


def rational(q):
    with localcontext() as ctx:
        ctx.prec = 90
        return {"numerator": str(q.numerator), "denominator": str(q.denominator),
                "decimal": str(Decimal(q.numerator) / Decimal(q.denominator))}


def segment(text, start, stop):
    i = text.index(start)
    j = text.index(stop, i)
    return text[i:j]


def replace(text, old, new, count):
    assert text.count(old) == count, (old, text.count(old), count)
    return text.replace(old, new)


def main():
    texts = {}
    provenance = {}
    for name, expected in PINNED.items():
        path = SOURCES / name / "Solution.lean"
        raw = path.read_bytes()
        assert digest(raw) == expected, (name, digest(raw))
        texts[name] = raw.decode("utf-8")
        assert "\r" not in texts[name], name
        provenance[name] = {"source": str(path), "sha256": expected, "bytes": len(raw)}
    base = texts["attempt-021"]
    ours = texts["master-of-puppets3"]
    shi = texts["shi-anchor-variance-refinement-2026"]
    old_block = segment(base, "theorem taylor12_F (", "theorem aInf_eq :")
    own_block = segment(ours, "theorem taylor20_F (", "theorem aInf_eq :")
    new_block = replace(own_block, "672168410564118872 / 10 ^ 18",
                        "672168410564118872522651 / 10 ^ 24", 2)
    assert new_block == segment(shi, "theorem taylor20_F (", "theorem aInf_eq :")

    # The transplanted block has exactly the same AM window and HW inputs.
    dependency_spans = [
        ("def cAMn :", "def ωAM ("),
        ("def dAM (", "theorem kernel_vAM"),
        ("def PAM :", "theorem energy_total :"),
        ("def HW :", "end AMW"),
    ]
    dependency_checks = []
    for start, stop in dependency_spans:
        expected = segment(base, start, stop)
        assert expected == segment(ours, start, stop), start
        assert expected == segment(shi, start, stop), start
        dependency_checks.append({"start": start, "stop": stop,
                                  "sha256": digest(expected.encode("utf-8"))})

    # Independently reproduce every rational inequality used by the enclosure.
    coeff_text = segment(base, "def cAMn :", "def cAM (j :")
    coeff = {int(k): int(v) for k, v in re.findall(r"\|\s*(\d+)\s*=>\s*(-?\d+)", coeff_text)}
    assert set(coeff) == set(range(13)) and coeff[0] == 10**9
    rlo = Q(7071067811865475244, 10**19)
    rhi = Q(7071067811865475245, 10**19)
    pihi = Q(314159265358979323847, 10**20)
    cos_hi = Q(95030574634453769, 125000000000000000)
    sin_lo = Q(649636939080062443, 10**18)
    error = Q(21, 20 * factorial(20))
    assert error == Q(1, 2317049531596800000)
    taylor_hi = sum((Q((-1)**k) * rlo**(2*k) / factorial(2*k)
                    for k in range(10)), Q(0)) + rlo**20 * error
    assert 0 < rlo < rhi < 1 and rlo*rlo <= Q(1, 2) <= rhi*rhi
    assert 0 < taylor_hi <= cos_hi < 1
    assert 0 < sin_lo and cos_hi*cos_hi + sin_lo*sin_lo <= 1
    assert sin_lo.numerator == isqrt(10**36 - (cos_hi * 10**18).numerator**2)
    pam_hi = sum((Q(coeff[k], 10**9)**2 * (Q(1, 2) - 1/(4*pihi*pihi*k*k))
                  for k in range(1, 13)), Q(0))
    numeric_h = Q(3, 2) - cos_hi/(2*rlo*sin_lo) - pam_hi/(2*sin_lo*sin_lo)
    assert 0 <= pam_hi and OLD_H < NEW_H <= numeric_h
    assert NEW_H.numerator == numeric_h.numerator * 10**24 // numeric_h.denominator
    assert (OLD_H - B)/(1 - C_FLOOR) == OLD_SCORE
    assert 0 < C_FLOOR <= Q(1, 64) < 1 and B >= 0
    assert OLD_SCORE < SCORE < 1
    assert SCORE == Q(667801670564118872522651, 991436180000000000000000)
    assert SCORE - OLD_SCORE == Q(7244924522651, 991436180000000000000000)

    # User-authorized removal of their obsolete first header; all other notices stay.
    assert base.startswith(OWNED_OLD_HEADER)
    top, body = base.split("import ChallengeDeps\n", 1)
    retained_top = top[len(OWNED_OLD_HEADER):]
    body = "import ChallengeDeps\n" + body
    body = replace(body, old_block, NOTICE + new_block, 1)
    replacements = [
        ("672168410556873948 / 10 ^ 18", "672168410564118872522651 / 10 ^ 24", 1),
        ("672168410556873948 / 1000000000000000000",
         "672168410564118872522651 / 1000000000000000000000000", 16),
        ("166950417639218487 / 247859045000000000",
         "667801670564118872522651 / 991436180000000000000000", 5),
    ]
    for old, new, count in replacements:
        body = replace(body, old, new, count)
    candidate = retained_top + body
    assert candidate.startswith(retained_top + "import ChallengeDeps\n")

    # Inverse transformation is an exhaustive allowlist of all source differences.
    inverted = body
    for old, new, count in reversed(replacements):
        # New HW power literals also occur twice in the substituted block.
        assert inverted.count(new) == count + (2 if "10 ^ 24" in new else 0)
        tail_start = inverted.index("theorem aInf_eq :")
        inverted = inverted[:tail_start] + replace(inverted[tail_start:], new, old, count)
    inverted = replace(inverted, NOTICE + new_block, old_block, 1)
    assert (OWNED_OLD_HEADER + retained_top + inverted).encode("utf-8") == base.encode("utf-8")

    # Existing block comments include licenses, attribution and historical changes.
    retained_original = base[len(OWNED_OLD_HEADER):]
    inherited_comments = re.findall(r"/-.*?-/", retained_original, flags=re.DOTALL)
    assert all(candidate.count(comment) >= retained_original.count(comment) for comment in inherited_comments)
    assert not re.search(r"^\s*(axiom|unsafe\s|opaque\s)", candidate, flags=re.MULTILINE)
    cert_start = "namespace RiemannFail\n"
    cert_stop = "end RiemannFail\n"
    assert segment(base, cert_start, cert_stop) == segment(candidate, cert_start, cert_stop)

    raw = candidate.encode("utf-8")
    assert len(raw) < 2_000_000
    target = HERE / "Candidate_taylor20_9point.lean"
    target.write_bytes(raw)
    diff = "".join(unified_diff(base.splitlines(keepends=True), candidate.splitlines(keepends=True),
                                fromfile="attempt-021/Solution.lean", tofile=target.name))
    (HERE / "candidate_allowlisted.diff").write_text(diff, encoding="utf-8", newline="\n")
    audit = {
        "verification": "EXACT ARITHMETIC AND SOURCE AUDIT ONLY; NO LEAN OR COMPARATOR REPLAY",
        "candidate": {"path": str(target), "sha256": digest(raw), "bytes": len(raw)},
        "sources": provenance,
        "score": rational(SCORE), "old_score": rational(OLD_SCORE),
        "gain_over_attempt_021": rational(SCORE - OLD_SCORE),
        "H": rational(NEW_H), "numeric_H": rational(numeric_h),
        "H_slack": rational(numeric_h - NEW_H),
        "cos_hi": rational(cos_hi), "sin_lo": rational(sin_lo),
        "cos_Taylor_upper": rational(taylor_hi),
        "circle_slack": rational(1 - cos_hi*cos_hi - sin_lo*sin_lo),
        "B": rational(B), "c": rational(C_FLOOR), "PAMhi": rational(pam_hi),
        "window_dependency_blocks_identical_across_three_sources": dependency_checks,
        "inverse_transform_recovers_source_bytes": True,
        "all_remaining_inherited_block_comments_retained": True,
        "removed_user_owned_optional_first_header": {
            "authorization": "Parent relayed user's already-established removal of this obsolete owned header",
            "sha256": digest(OWNED_OLD_HEADER.encode("utf-8")),
            "bytes": len(OWNED_OLD_HEADER.encode("utf-8")),
            "text": OWNED_OLD_HEADER,
        },
        "nine_point_concrete_certificate_unchanged": True,
        "new_block_equals_accepted_Shi_window_block": True,
        "allowed_downstream_replacements": [
            {"old": old, "new": new, "count": count} for old, new, count in replacements],
        "counted_zero_exports": {
            "dyadic": "(candidateKappa - epsilon) * Ncount T (2*T) <= N0star T (2*T)",
            "cumulative": "(candidateKappa - epsilon) * Ncount 0 T <= N0star 0 T",
            "quantifiers": "forall epsilon > 0, exists T0, forall T >= T0",
            "underlying_chain": "N0simple lower bound implies distinct-critical-line N0star bound",
            "trusted_constants": "candidateKappa and currentRecordKappa remain imported from ChallengeDeps.CandidateSpec",
        },
    }
    (HERE / "candidate_exact_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: audit[key] for key in ("verification", "candidate", "score", "gain_over_attempt_021")}, indent=2))


if __name__ == "__main__":
    main()
