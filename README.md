# AutoMulti Revision Submission Repository

This repository contains the public submission artifacts for the revised
AutoMulti manuscript. It is intended to be used directly as the GitHub
repository cited in the revised manuscript and response letter.

## Contents

- `packages/AutoMulti-windows-x64-20260609_revision_submission.zip`: the
  current Windows x64 AutoMulti compiled binary package used for this revision.
- `packages/AutoMulti-windows-x64-20260609_revision_submission.sha256.txt`:
  SHA256 checksum for the Windows package.
- `packages/AutoMulti-windows-x64-20260609_revision_submission.README.txt`:
  short package usage notes.
- `LICENSE_AUTOMULTI_EULA.txt`: the proprietary End User License Agreement
  governing the AutoMulti compiled binary package.
- `THIRD_PARTY_NOTICES.md`: third-party component notices for the distributed
  binary package.
- `QT_LGPL_RELINKING.md`: replacement/relinking information for the LGPL
  PySide6/Qt runtime libraries included in the binary package.
- `AutoMulti-ML-testing-package/`: the companion ML reproducibility package
  containing the fixed test structures, frozen model weights, and inference
  script used in the diimine-Ni case study.
- `REVIEWER_INSTRUCTIONS.txt`: short submission-system text for reviewers.
- `verify_repository_package.ps1`: local repository integrity check.

## Distribution Scope

AutoMulti is distributed here as a publicly downloadable Windows x64 compiled
desktop application under a proprietary End User License Agreement (EULA). This
submission repository does not include AutoMulti source code, tests, build
scripts, or the development repository. The repository is intended to support
software accessibility, peer review, and scholarly verification of the revised
manuscript.

The AutoMulti package may interoperate with external programs such as xTB,
Multiwfn, Gaussian, and ORCA, but those programs are not redistributed here and
must be obtained and installed separately under their own licenses.

## Windows Application

1. Confirm the Windows package exists at
   `packages/AutoMulti-windows-x64-20260609_revision_submission.zip`.
2. Unzip the package.
3. Keep the extracted `AutoMulti/` directory structure unchanged.
4. Run `AutoMulti/AutoMulti.exe`.

To verify the package checksum from the repository root:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath .\packages\AutoMulti-windows-x64-20260609_revision_submission.zip
```

Expected SHA256:

```text
39F2895668DE5767C6958BB6FB7DAEE54EB6390047544EC3995AE3582B0E44DA
```

## Companion ML Reproducibility Package

The companion ML package is a downstream reproducibility artifact, not an
AutoMulti GUI module. It provides the fixed test inputs, anonymized structure
files, frozen five-fold model weights, and inference script used to reproduce
the reported SchNet test-set performance.

From `AutoMulti-ML-testing-package/`, run:

```powershell
python scripts\runtest_final_dataset.py --mode ensemble --split test
```

Expected output:

```text
ensemble split=test r2=0.911604 rmse=0.831564 mae=0.544736
```

The ML result reproduces internally consistent GFN2-xTB labels and should not
be interpreted as DFT or experimental validation.

## Repository Check

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\verify_repository_package.ps1
```

To also run the ML inference check:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\verify_repository_package.ps1 -RunInference
```
