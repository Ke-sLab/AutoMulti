# Machine-readable test coordinates

This directory provides editable coordinate files for the fixed 777-structure test set.

- `test_xyz/`: one XYZ file per anonymized 8-digit molecule ID.
- `test_coordinates.xyz`: concatenated XYZ file for the same 777 structures.
- `test_coordinates.csv`: atom-level table with `mol_id`, `atom_index`, `element`, `x`, `y`, and `z` columns.
- `mol_files/`: original MOL files used by the inference script.

The numeric IDs match `dataset/test_inputs.csv` and the manuscript Supporting Information.
