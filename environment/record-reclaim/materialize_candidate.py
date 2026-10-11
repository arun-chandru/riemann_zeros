#!/usr/bin/env python3
"""Reconstruct the pinned, single-file circle-enclosure submission.

Standard library only. The input and final output are both hash pinned.
This program reconstructs source; Lean verification is a separate step.
"""

import argparse
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_URL = (
    "https://raw.githubusercontent.com/josusanmartin/riemann/"
    "6fd487c526acbfb0f76d44772614454b7289f9e6/"
    "submissions/shi-exact-window-refinement-2026/proof/Solution.lean"
)
SOURCE_SHA256 = "e77b8cbcf09949fbe2b8729d04956c0c1048e512acac9a65ba4a36a7abc85052"
SOURCE_SIZE = 1859323
OUTPUT_SHA256 = "f35bfd108dac8504346ee3f7a7e9b6890b36fb5ca46c6fe83b5097e76b656548"
OUTPUT_SIZE = 1860982

HEADER = """/-
R. Arun Chandru
arun.chandru@gmail.com
https://github.com/arun-chandru
https://x.com/arunchandru
https://researchgate.net/profile/R_Chandru

Copyright (c) 2026 R. Arun Chandru, for the circle-enclosure refinement.
SPDX-License-Identifier: Apache-2.0

Critical-line proportion: 167031227639218487/247987190000000000.

This refinement sharpens the existing order-twelve cosine enclosure and
uses sin(theta)^2 + cos(theta)^2 = 1, with proved positivity, to sharpen
the sine lower bound. The resulting exact window floor is
672168410556873948/10^18. The inherited matching, certificate, and
zero-count argument propagates this floor to the displayed rational.
No window coefficients, certificate data, analytic hypotheses, or counting
definitions are changed. This is an enclosure improvement, not a new
analytic or spectral method.

Base source: Yuhang Shi's exact-window refinement at
josusanmartin/riemann@6fd487c526acbfb0f76d44772614454b7289f9e6,
submissions/shi-exact-window-refinement-2026/proof/Solution.lean.
Shi's refinement builds on R. Arun Chandru's master-of-puppets submission,
Samuel Lavery's certificate, and the other attributed works below.
All inherited notices and license texts are retained. Their descriptions,
including draft and numerical statements, refer to their historical versions.
-/
"""

SIN_PROOF = """theorem sin_theta0_ge : 162409234769194159 / 250000000000000000 ≤ Real.sin (Real.sqrt 2 / 2) := by
 have hb := sqrt2_half_bounds
 have hc := cos_theta0_le
 have hc0 : 0 ≤ Real.cos (Real.sqrt 2 / 2) :=
   Real.cos_nonneg_of_mem_Icc ⟨by linarith [hb.1, Real.pi_gt_three], by linarith [hb.2, Real.pi_gt_three]⟩
 have hcsq : Real.cos (Real.sqrt 2 / 2) ^ 2 ≤ (190061149269609477 / 250000000000000000 : ℝ) ^ 2 :=
   pow_le_pow_left₀ hc0 hc 2
 have hcircle := Real.sin_sq_add_cos_sq (Real.sqrt 2 / 2)
 have hs0 := sin_theta0_pos
 have hsq : (162409234769194159 / 250000000000000000 : ℝ) ^ 2 ≤ Real.sin (Real.sqrt 2 / 2) ^ 2 := by
   nlinarith only [hcsq, hcircle]
 nlinarith only [hsq, hs0]
"""


def reconstruct(raw):
    if len(raw) != SOURCE_SIZE or sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Pinned source size or SHA256 mismatch")
    source = raw.decode("utf-8")
    header_end = source.index("-/") + 2
    historical, body = source[:header_end], source[header_end:]
    replacements = [
        ("672168410508 / 10 ^ 12", "672168410556873948 / 10 ^ 18", 3),
        ("672168410508 / 1000000000000", "672168410556873948 / 1000000000000000000", 6),
        ("15184657057 / 22544290000", "167031227639218487 / 247987190000000000", 4),
        ("76024459708 / 10 ^ 11", "190061149269609477 / 250000000000000000", 4),
        ("64963693904 / 10 ^ 11", "162409234769194159 / 250000000000000000", 9),
    ]
    for old, new, count in replacements:
        if body.count(old) != count:
            raise ValueError("Unexpected replacement count for " + old)
        body = body.replace(old, new)
    if body.count("theorem sin_theta0_ge :") != 1:
        raise ValueError("Sine theorem is missing or ambiguous")
    start = body.index("theorem sin_theta0_ge :")
    end = body.index("def PAMhi :", start)
    body = body[:start] + SIN_PROOF + body[end:]
    return (HEADER + historical + body).encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Use a local copy of the pinned input")
    parser.add_argument("--output", type=Path, default=Path("r_arun_chandru_proof.lean"))
    args = parser.parse_args()
    if args.source:
        raw = args.source.read_bytes()
    else:
        request = Request(SOURCE_URL, headers={"User-Agent":"circle-enclosure-replay/1"})
        with urlopen(request, timeout=60) as response:
            raw = response.read()
    result = reconstruct(raw)
    digest = sha256(result).hexdigest()
    if len(result) != OUTPUT_SIZE or digest != OUTPUT_SHA256:
        raise ValueError("Reconstructed output mismatch: " + str(len(result)) + " " + digest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print(str(args.output) + " " + str(len(result)) + " " + digest)


if __name__ == "__main__":
    main()
