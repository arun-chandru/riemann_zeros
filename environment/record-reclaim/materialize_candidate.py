#!/usr/bin/env python3
"""Reconstruct one exact hash-pinned candidate, without running Lean.

The two transformation modules use only the Python standard library. The
original source, intermediate source, and final source are hash checked.
"""
import argparse
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen

import window_candidate
import certificate_candidate

SOURCE_URL = (
    "https://raw.githubusercontent.com/josusanmartin/riemann/"
    "e072ab396e34fd937224ff3f666d3d7a5db9fb18/"
    "submissions/attempt-020/proof/Solution.lean"
)
SOURCE_HASH = "704f3b488692e4f990ffefec34b7f9f39a632594cca2bc7e55d35c3e041dce6e"
INTERMEDIATE_HASH = "9f27d659b6452a4c670ad02c9d6121dbb9df3ab5c4890c0abb1408bf456177f8"
OUTPUT_HASH = "12c688f5330dada28515c5bae838eaeaa01ebe57cc96d3b1b4239d02f0fa1da2"
OUTPUT_BYTES = 1729083
PUBLIC_HASH = "9dea76f4d5145278a5ff1b52f0609a227d0148aae542e56fb41720b6c2e94b63"
PUBLIC_BYTES = 1727667

PUBLIC_HEADER = b'''/-
R. Arun Chandru
arun.chandru@gmail.com
https://github.com/arun-chandru
https://x.com/arunchandru
https://researchgate.net/profile/R_Chandru

Copyright (c) 2026 R. Arun Chandru, for original contributions.
SPDX-License-Identifier: Apache-2.0

Modified by R. Arun Chandru, 2026-10-12.
Critical-line proportion: 6424046928501143/9537623075000000.
Derived from Samuel Lavery's attempt-020; inherited notices follow.
-/
'''


def public_source(raw):
    """Replace only the two new optional headers; preserve inherited notices."""
    if len(raw) != OUTPUT_BYTES or sha256(raw).hexdigest() != OUTPUT_HASH:
        raise ValueError("Audited input mismatch")
    first, second, inherited = raw.split(b'-/\n', 2)
    assert first.startswith(b'/-\nR. Arun Chandru\n')
    assert second.startswith(b'/-\nR. Arun Chandru\n')
    assert inherited.startswith(b'/-\nR. Arun Chandru\n')
    result = PUBLIC_HEADER + inherited
    marker = b'import ChallengeDeps\n'
    assert result[result.index(marker):] == raw[raw.index(marker):]
    assert len(result) == PUBLIC_BYTES and sha256(result).hexdigest() == PUBLIC_HASH
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("r_arun_chandru_proof.lean"))
    args = parser.parse_args()
    if args.source:
        raw = args.source.read_bytes()
    else:
        request = Request(SOURCE_URL, headers={"User-Agent":"exact-enclosure-replay/1"})
        with urlopen(request, timeout=60) as response:
            raw = response.read()
    if sha256(raw).hexdigest() != SOURCE_HASH:
        raise ValueError("Pinned accepted source SHA256 mismatch")
    report = window_candidate.build(raw, 20)
    intermediate = Path(report["path"]).read_bytes()
    if sha256(intermediate).hexdigest() != INTERMEDIATE_HASH:
        raise ValueError("Intermediate enclosure source SHA256 mismatch")
    final = certificate_candidate.transform(intermediate)
    if len(final) != OUTPUT_BYTES or sha256(final).hexdigest() != OUTPUT_HASH:
        raise ValueError("Final candidate size or SHA256 mismatch")
    final = public_source(final)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(final)
    print(str(args.output), len(final), sha256(final).hexdigest())


if __name__ == "__main__":
    main()
