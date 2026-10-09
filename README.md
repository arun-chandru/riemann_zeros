# A formal lower bound, 67.3547805%, for distinct critical-line zeros of the Riemann zeta function

R. Arun Chandru  
Email: arun.chandru@gmail.com  


## Abstract

The nontrivial zeros of the Riemann zeta function lie in a vertical strip in the complex plane. Its critical line is the line with real part one half. The Riemann Hypothesis asserts that every nontrivial zero lies on that line. This project concerns a quantitative lower bound; it does not prove the Riemann Hypothesis.

The formalization gives the exact asymptotic bound

$$
\kappa=\frac{66812491}{99194876}
       =0.673547805029767868\ldots,
$$

approximately 67.3547805%, for distinct critical-line zeros relative to all nontrivial zeros counted with multiplicity. The distinction matters: a multiple zero contributes once to the numerator and according to its multiplicity to the denominator. The internal argument first controls simple critical-line zeros and then obtains the distinct-zero conclusion.

The proof reuses an existing, attributed eight-point numerical certificate and analytic window. An additional same-operator transfer combines spectral control of separated Gram-matrix blocks, close-pair matching, and pinching to retain the full matrix defect used by the counting argument. Sparse error accounting charges approximation errors only to the relevant finite-neighbour band, keeping that cost proportional to the number of retained points. The resulting defect estimate is composed with the inherited certificate and analytic zero-counting framework.

The conclusion covers both dyadic height windows and cumulative windows. For every positive tolerance, the bound holds above some height; no numerical threshold or uniform assertion for every small window is supplied. The inherited certificate is not claimed as newly discovered or newly generated here. The adaptation and its source credits are mentioned below.

## Method

> Gram-defect pinching and separation

## Summary

> Proves unconditionally at least 67.3547805% distinct critical-line zeros asymptotically, relative to all zeros counted with multiplicity. Separated-block spectral control and close-pair matching retain the full Gram defect using an existing eight-point certificate; both counting windows are covered.

## Exact theorem and counting convention

`N(a,b)` counts all nontrivial zeros with imaginary part in `(a,b]`, with multiplicity. `N0*(a,b)` counts distinct zeros in that interval on `Re(s)=1/2`. For every real `epsilon > 0`, there is a real `T0` such that every real `T >= T0` satisfies

$$
(\kappa-\epsilon)N(T,2T)\le N_0^*(T,2T),
\qquad
(\kappa-\epsilon)N(0,T)\le N_0^*(0,T).
$$

## Proof file

The formalization is in r_arun_chandru_proof.lean.

- Numerator: `66812491`; denominator: `99194876`.
- Source: 1,858,713 bytes, UTF-8 LF without BOM.

`.gitattributes` preserves LF line endings in Git. Upload the exact hashed proof bytes without editor reformatting.

```sh
npx tsx scripts/prepare-candidate.ts <submission-directory> <fresh-zeta23-workspace>
npx tsx scripts/verify-submission.ts <submission-directory> --mode=prepare
npx tsx scripts/verify-submission.ts <submission-directory> --mode=full
```
## Attribution, adaptation and license

The analytic window and exact eight-point certificate are inherited from Samuel Lavery's [published attempt-016 proof](https://github.com/josusanmartin/riemann/blob/296f7bb9c4e01b0c97554cf76af91ed99a410e8d/submissions/attempt-016/proof/Solution.lean). The original detailed copyright/transitive-credit block is retained. This adaptation claims no priority for the certificate, its numerical optimization or every intermediate method.

The same-operator full-defect transfer and its composition are the additional adaptation documented here. Attributed ingredients include Kristian Muri Knausgard's [formal development](https://github.com/kristianmk/839/tree/0e961ea199b425010843bc8044676d4ad29fe031/lean), [Anthropic Zeta23](https://github.com/anthropics/zeta-23-lean/tree/3635e74826a4c1fcece7d1cd2b6fa75e43a00510), [AMTOPA's window-family work](https://github.com/AMTOPA/zeta-exact-pressure/tree/7253fdcab9366af45b8c8caf44e408c0af44a1a7), and [Thomas Lince's Zeta Lab bridge](https://github.com/teal-sea/zeta-lab/tree/aa6af68acd48466e9b005b80aaf608036de44c99). The proof contains specific change notices and more inherited credits.

New contributions are offered under [Apache-2.0](LICENSE). Incorporated portions retain their applicable notices/terms, including MIT notices; see [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt) and the embedded notices.

## Note on AI use

The author declares the substantial use of consumer-grade Gemini-3 and GPT-6 models for literature search, exploring and developing ideas, codes and proofs, drafting and LaTeX typesetting; the author takes full and sole responsibility for all contents of this work.
