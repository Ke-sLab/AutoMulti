# AutoMulti ML Inference Test Package

This package contains the files needed to rerun the frozen AutoMulti ML test-set inference.

## Contents

- `dataset/test_inputs.csv`: fixed test-set IDs, reference barriers, and descriptor inputs
- `dataset/mol_files/`: numeric-ID MOL files used by `test_inputs.csv`
- `dataset/features/barrier_atom_features_basic.npz`: atom-feature cache used by `test_inputs.csv`
- `model/fold_0/best_model.pt` to `model/fold_4/best_model.pt`: frozen ensemble weights
- `scripts/runtest_final_dataset.py`: inference entrypoint
- `requirements.txt`: Python package requirements

All public molecule IDs are anonymized 8-digit numeric IDs.

## Run

From the package root:

```powershell
python scripts\runtest_final_dataset.py --mode ensemble --split test
```

Expected output:

```text
ensemble split=test r2=0.911604 rmse=0.831564 mae=0.544736
```

To run one fold:

```powershell
python scripts\runtest_final_dataset.py --mode per_fold --fold-index 0 --split test
```

To export predictions:

```powershell
python scripts\runtest_final_dataset.py --mode ensemble --split test --output-csv predictions.csv
```
