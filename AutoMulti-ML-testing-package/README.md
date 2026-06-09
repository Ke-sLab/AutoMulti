# Companion ML Reproducibility Package for the AutoMulti Case Study

This companion package contains the files needed to rerun the downstream SchNet inference test and inspect the fixed test structures used in the diimine-Ni case study. It is not an AutoMulti module and is not part of the AutoMulti executable or GUI functionality; AutoMulti provides the generated structures, xTB-derived labels, descriptors, and machine-readable exports used by this separate reproducibility package.

## Contents

- `dataset/test_inputs.csv`: fixed test-set IDs, GFN2-xTB reference barriers, and descriptor inputs
- `dataset/mol_files/`: numeric-ID MOL files used by `test_inputs.csv`
- `dataset/test_xyz/`: editable per-structure XYZ files for the same 777 test molecules
- `dataset/test_coordinates.xyz`: concatenated XYZ coordinate file
- `dataset/test_coordinates.csv`: atom-level coordinate table
- `dataset/features/barrier_atom_features_basic.npz`: atom-feature cache used by `test_inputs.csv`
- `model/fold_0/best_model.pt` to `model/fold_4/best_model.pt`: frozen ensemble weights
- `scripts/runtest_final_dataset.py`: inference entrypoint
- `requirements.txt`: Python package requirements

All public molecule IDs are anonymized 8-digit numeric IDs. The model reproduces GFN2-xTB labels and is not a DFT or experimental validation benchmark.

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
