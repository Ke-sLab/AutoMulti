# AutoMulti Packaged Application and ML Testing Package

This repository contains two public-facing AutoMulti artifacts:

- `AutoMulti-ML-testing-package/`: inference-only ML testing package.
- `packages/AutoMulti-windows-x64-20260425_223350.zip`: packaged Windows x64 application.

Large binary files are tracked with Git LFS. Install Git LFS before cloning or pushing this repository.

## Windows Application

1. Download or clone the repository with Git LFS enabled.
2. Unzip `packages/AutoMulti-windows-x64-20260425_223350.zip`.
3. Keep the extracted `AutoMulti/` directory structure unchanged.
4. Run `AutoMulti/AutoMulti.exe`.

Checksum:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath .\packages\AutoMulti-windows-x64-20260425_223350.zip
```

Compare the result with `packages/AutoMulti-windows-x64-20260425_223350.sha256.txt`.

## ML Testing Package

The ML package is stored as an unpacked folder so reviewers can inspect the input data, script, and model weights directly. It contains only inference resources:

- fixed test inputs
- numeric-ID MOL files
- atom-feature cache
- frozen five-fold model weights
- inference script
- Python requirements

From `AutoMulti-ML-testing-package/`, run:

```powershell
python scripts\runtest_final_dataset.py --mode ensemble --split test
```

Expected output:

```text
ensemble split=test r2=0.911604 rmse=0.831564 mae=0.544736
```

## Repository Setup

For a new GitHub repository:

```powershell
git init
git lfs install
git add .gitattributes README.md AutoMulti-ML-testing-package packages
git commit -m "Add AutoMulti packaged app and ML testing package"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

If you copy these files into an existing repository, keep `.gitattributes` at the repository root before running `git add`.
