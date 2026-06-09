# Publish This Submission Repository

This folder is intended to be the root of the public GitHub repository cited by
the revised AutoMulti manuscript.

The public repository should contain:

- the `AutoMulti-windows-x64-20260609_revision_submission.zip` Windows onedir
  binary package as the only primary AutoMulti executable package
- the companion `AutoMulti-ML-testing-package/`
- the proprietary EULA and required third-party compliance documents

Do not push AutoMulti source code, build directories, development caches, or
older historical binary packages into this submission repository.

## One-time Setup

Create a public GitHub repository, for example:

```text
AutoMulti-revision-submission
```

Then run these commands from this directory:

```powershell
git init
git lfs install
git add .gitattributes
git add .
git commit -m "Add AutoMulti revision submission repository"
git branch -M main
git remote add origin https://github.com/Ke-sLab/AutoMulti.git
git push -u origin main
```

Before pushing, confirm Git LFS is tracking the large files:

```powershell
git lfs ls-files
```

Expected LFS-tracked paths include:

- `packages/AutoMulti-windows-x64-20260609_revision_submission.zip`
- `AutoMulti-ML-testing-package/model/fold_0/best_model.pt` through `fold_4/best_model.pt`
- `AutoMulti-ML-testing-package/dataset/features/barrier_atom_features_basic.npz`

## GitHub Archive Setting

In the GitHub repository settings, enable:

```text
Include Git LFS objects in archives
```

This matters only for users who download GitHub's generated source ZIP/TAR
archive. Cloning with Git LFS and running `git lfs pull` remains the preferred
workflow.

## Submission System

After the repository is public, copy the text in `REVIEWER_INSTRUCTIONS.txt`
into the journal submission system.
