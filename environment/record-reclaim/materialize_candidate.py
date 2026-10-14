"""Reconstruct exactly the frozen candidate from two public pinned proofs."""
import argparse
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
import window_candidate
import certificate_candidate

PINS = {
    'attempt-022':'72e3123e7bf235a697dd97d976738afdefdcf257',
    'lixiang90-nine-point-refinement':'aa868dc8e4c46e7dda5ac21c47e1c53e1a122b91',
}
FINAL_SHA = '286f009e7ac83e9529cecc603fa8a63e6d3a7c8b38dd09ccc91bd411856c6327'
FINAL_BYTES = 1942932

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('r_arun_chandru_proof.lean'))
    parser.add_argument('--cached-sources',type=Path)
    args=parser.parse_args()
    sources={}
    for name,pin in PINS.items():
        if args.cached_sources:
            sources[name]=(args.cached_sources/name/'proof/Solution.lean').read_bytes()
        else:
            url=f'https://raw.githubusercontent.com/josusanmartin/riemann/{pin}/submissions/{name}/proof/Solution.lean'
            with urlopen(Request(url,headers={'User-Agent':'exact-proof-replay/1'}),timeout=90) as response:
                sources[name]=response.read()
    intermediate=window_candidate.transform(sources['attempt-022'],sources['lixiang90-nine-point-refinement'])
    result,report=certificate_candidate.transform(intermediate)
    assert len(result)==FINAL_BYTES and sha256(result).hexdigest()==FINAL_SHA
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(result)
    print(str(args.output),len(result),sha256(result).hexdigest())

if __name__=='__main__':
    main()
