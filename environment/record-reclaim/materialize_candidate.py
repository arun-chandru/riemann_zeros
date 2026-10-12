"""Download pinned accepted inputs, reconstruct, and hash-check one candidate."""
import argparse
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
import window_candidate
import certificate_candidate

PINS = {
    "attempt-021": "8998f2005d202e4a0a406c8c7507426435466d38",
    "shi-anchor-variance-refinement-2026": "431cd7d7e2b799a1f41f86e28e75d7f9cd933d34",
    "master-of-puppets3": "839d0da2316f481c8036f6aa5a94bfd0dbef16ef",
}
WINDOW_HASH = "4253579322da07f6196c81d3eb2329740669711656b66d3ffd9f1eed6b68265a"
FINAL_HASH = "779f9ff3b4c3eb2c6b6af7c393adf5768e944cbbdf47e6203f80e93f0664e15c"
FINAL_BYTES = 1930898


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("r_arun_chandru_proof.lean"))
    parser.add_argument("--cached-sources", type=Path)
    args = parser.parse_args()
    for name, commit in PINS.items():
        if args.cached_sources:
            raw = (args.cached_sources / name / "Solution.lean").read_bytes()
        else:
            url = f"https://raw.githubusercontent.com/josusanmartin/riemann/{commit}/submissions/{name}/proof/Solution.lean"
            with urlopen(Request(url, headers={"User-Agent": "exact-nine-point-replay/1"}), timeout=90) as response:
                raw = response.read()
        assert sha256(raw).hexdigest() == window_candidate.PINNED[name], name
        target = window_candidate.SOURCES / name / "Solution.lean"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    window_candidate.main()
    intermediate = (window_candidate.HERE / "Candidate_taylor20_9point.lean").read_bytes()
    assert sha256(intermediate).hexdigest() == WINDOW_HASH
    result = certificate_candidate.transform(intermediate)
    assert len(result) == FINAL_BYTES and sha256(result).hexdigest() == FINAL_HASH
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print(args.output, len(result), sha256(result).hexdigest())


if __name__ == "__main__":
    main()
