# AutoMulti Packaged Application and ML Testing Package

This repository contains two public-facing AutoMulti artifacts:

- `AutoMulti-ML-testing-package/`: inference-only ML testing package.


Large binary files are tracked with Git LFS. Install Git LFS before cloning or pushing this repository.



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
