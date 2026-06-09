from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import torch
from rdkit import Chem, RDLogger
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from torch import nn
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn.models import SchNet


SCRIPT_PATH = Path(__file__).resolve()
PACKAGE_ROOT = SCRIPT_PATH.parents[1]

DESCRIPTOR_COLUMNS = ["qm__HL_gap", "qm__delta_SCC_IP"]
ATOM_FEATURE_COLUMNS = ["charge", "f_minus", "f_plus", "f_zero"]
BATCH_SIZE = 16

MODEL_CONFIG = {
    "hidden_channels": 256,
    "num_filters": 128,
    "num_interactions": 6,
    "num_gaussians": 100,
    "cutoff": 9.904100592323905,
    "atom_feature_hidden": 64,
    "atom_mix_hidden": 64,
    "fusion_hidden": 256,
    "atom_injection": "scalar_gate",
}

FOLD_CONFIGS = {
    0: {
        "descriptor_means": [0.050902876803000346, 8.123521828613036],
        "descriptor_stds": [0.05390184119931539, 0.23514269620389014],
        "atom_feature_means": [
            -1.439531133184957e-11,
            -0.014133651740849018,
            -0.014136668294668198,
            -0.014135953038930893,
        ],
        "atom_feature_stds": [
            0.11308559775352478,
            0.02869759500026703,
            0.025083016604185104,
            0.02599092200398445,
        ],
    },
    1: {
        "descriptor_means": [0.05096640824553232, 8.126208018757486],
        "descriptor_stds": [0.053986716521269504, 0.23255315003784213],
        "atom_feature_means": [
            -5.04173352372517e-12,
            -0.014122509397566319,
            -0.014126325026154518,
            -0.014124167151749134,
        ],
        "atom_feature_stds": [
            0.11292100697755814,
            0.028636883944272995,
            0.025035368278622627,
            0.025928905233740807,
        ],
    },
    2: {
        "descriptor_means": [0.05025595938900456, 8.125525455351998],
        "descriptor_stds": [0.053437690700706024, 0.23140408954563743],
        "atom_feature_means": [
            -2.24597094394818e-11,
            -0.014085319824516773,
            -0.0140881622210145,
            -0.01408762764185667,
        ],
        "atom_feature_stds": [
            0.11296242475509644,
            0.028596926480531693,
            0.024955030530691147,
            0.025867361575365067,
        ],
    },
    3: {
        "descriptor_means": [0.051528019086854525, 8.126178512250744],
        "descriptor_stds": [0.05454510464677582, 0.23331173691931706],
        "atom_feature_means": [
            -1.82355085892594e-11,
            -0.014218557626008987,
            -0.014222652651369572,
            -0.01422096323221922,
        ],
        "atom_feature_stds": [
            0.11310383677482605,
            0.02886083722114563,
            0.02515624649822712,
            0.026108942925930023,
        ],
    },
    4: {
        "descriptor_means": [0.04980825082669638, 8.128516312958538],
        "descriptor_stds": [0.052904737834919995, 0.23525264356720002],
        "atom_feature_means": [
            -8.97113459907839e-12,
            -0.014139951206743717,
            -0.014141854830086231,
            -0.014141603372991085,
        ],
        "atom_feature_stds": [
            0.11320696026086807,
            0.028719643130898476,
            0.025028951466083527,
            0.02596675418317318,
        ],
    },
}


RDLogger.DisableLog("rdApp.*")


@dataclass
class AtomFeatureStore:
    sample_keys: np.ndarray
    atom_offsets: np.ndarray
    atom_numbers: np.ndarray
    atom_features: np.ndarray
    feature_names: list[str]

    def __post_init__(self) -> None:
        self.index_by_key = {str(key): idx for idx, key in enumerate(self.sample_keys.tolist())}

    def get_sample(self, sample_key: str) -> tuple[np.ndarray, np.ndarray] | None:
        idx = self.index_by_key.get(str(sample_key))
        if idx is None:
            return None
        start = int(self.atom_offsets[idx])
        stop = int(self.atom_offsets[idx + 1])
        return self.atom_numbers[start:stop], self.atom_features[start:stop]


@dataclass
class AtomFeatureStats:
    means: np.ndarray
    stds: np.ndarray


@dataclass
class DatasetBuildResult:
    dataset: list[Data]
    parse_failures: list[str]
    cache_missing: int
    alignment_failures: int
    total_rows: int

    @property
    def usable_rows(self) -> int:
        return len(self.dataset)


@dataclass
class FoldPrediction:
    fold_index: int
    metrics: dict[str, float | int]
    predictions: pd.DataFrame


class SchNetAtomEncoder(nn.Module):
    def __init__(
        self,
        hidden_channels: int,
        num_filters: int,
        num_interactions: int,
        num_gaussians: int,
        cutoff: float,
        atom_feature_dim: int,
        atom_feature_hidden: int,
        atom_injection: str,
        atom_mix_hidden: int,
    ) -> None:
        super().__init__()
        self.atom_feature_dim = int(atom_feature_dim)
        self.atom_injection = str(atom_injection)
        self.schnet = SchNet(
            hidden_channels=hidden_channels,
            num_filters=num_filters,
            num_interactions=num_interactions,
            num_gaussians=num_gaussians,
            cutoff=cutoff,
            max_num_neighbors=32,
            readout="add",
            dipole=False,
        )
        self.graph_dim = int(self.schnet.lin1.out_features)
        self.atom_feature_backbone = nn.Sequential(
            nn.Linear(atom_feature_dim, atom_feature_hidden),
            nn.ReLU(),
        )
        if self.atom_injection != "scalar_gate":
            raise ValueError(f"Unsupported atom feature mode: {self.atom_injection}")
        self.atom_gate_delta_proj = nn.Linear(atom_feature_hidden, hidden_channels)
        self.atom_gate_mlp = nn.Sequential(
            nn.Linear(hidden_channels + atom_feature_hidden, atom_mix_hidden),
            nn.ReLU(),
            nn.Linear(atom_mix_hidden, 1),
        )

    def inject_atom_features(self, atom_embeddings: torch.Tensor, atom_features: torch.Tensor) -> torch.Tensor:
        atom_latent = self.atom_feature_backbone(atom_features)
        delta = self.atom_gate_delta_proj(atom_latent)
        gate = torch.sigmoid(self.atom_gate_mlp(torch.cat([atom_embeddings, atom_latent], dim=-1)))
        return atom_embeddings + gate * delta

    def encode_graph(self, batch: Data) -> torch.Tensor:
        z = batch.z
        pos = batch.pos
        graph_batch = batch.batch
        h = self.schnet.embedding(z)
        atom_features = batch.atom_features.view(z.size(0), self.atom_feature_dim)
        h = self.inject_atom_features(h, atom_features)
        edge_index, edge_weight = self.schnet.interaction_graph(pos, graph_batch)
        edge_attr = self.schnet.distance_expansion(edge_weight)
        for interaction in self.schnet.interactions:
            h = h + interaction(h, edge_index, edge_weight, edge_attr)
        h = self.schnet.lin1(h)
        h = self.schnet.act(h)
        return self.schnet.readout(h, graph_batch, dim=0)


class SchNetFusionRegressor(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.descriptor_dim = len(DESCRIPTOR_COLUMNS)
        self.encoder = SchNetAtomEncoder(
            hidden_channels=int(MODEL_CONFIG["hidden_channels"]),
            num_filters=int(MODEL_CONFIG["num_filters"]),
            num_interactions=int(MODEL_CONFIG["num_interactions"]),
            num_gaussians=int(MODEL_CONFIG["num_gaussians"]),
            cutoff=float(MODEL_CONFIG["cutoff"]),
            atom_feature_dim=len(ATOM_FEATURE_COLUMNS),
            atom_feature_hidden=int(MODEL_CONFIG["atom_feature_hidden"]),
            atom_injection=str(MODEL_CONFIG["atom_injection"]),
            atom_mix_hidden=int(MODEL_CONFIG["atom_mix_hidden"]),
        )
        fusion_hidden = int(MODEL_CONFIG["fusion_hidden"])
        self.descriptor_encoder = nn.Sequential(
            nn.Linear(self.descriptor_dim, fusion_hidden),
            nn.ReLU(),
            nn.Linear(fusion_hidden, fusion_hidden),
            nn.ReLU(),
        )
        self.head = nn.Sequential(
            nn.Linear(self.encoder.graph_dim + fusion_hidden, fusion_hidden),
            nn.ReLU(),
            nn.Linear(fusion_hidden, 1),
        )

    def forward(self, batch: Data) -> torch.Tensor:
        graph_repr = self.encoder.encode_graph(batch)
        global_features = batch.global_features.view(batch.num_graphs, self.descriptor_dim)
        descriptor_repr = self.descriptor_encoder(global_features)
        fused = torch.cat([graph_repr, descriptor_repr], dim=-1)
        return self.head(fused).view(-1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the packaged AutoMulti ML inference test.")
    parser.add_argument("--mode", choices=["ensemble", "per_fold"], default="ensemble")
    parser.add_argument("--fold-index", type=int, default=0, help="Used with --mode=per_fold.")
    parser.add_argument("--split", choices=["test"], default="test", help="Only the fixed test set is packaged.")
    parser.add_argument("--dataset-csv", default="dataset/test_inputs.csv")
    parser.add_argument("--mol-dir", default="dataset/mol_files")
    parser.add_argument("--atom-feature-cache", default="dataset/features/barrier_atom_features_basic.npz")
    parser.add_argument("--model-root", default="model")
    parser.add_argument("--output-csv", default=None, help="Optional path for writing predictions.")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def resolve_package_path(raw: str | None, default: Path) -> Path:
    if not raw:
        return default
    path = Path(raw)
    return path if path.is_absolute() else PACKAGE_ROOT / path


def normalize_mol_id(value: object) -> str:
    text = str(value).strip()
    return text.zfill(8) if text.isdigit() else text


def resolve_device(raw: str | None) -> torch.device:
    if raw:
        return torch.device(raw)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_eval_rows(dataset_csv: Path, mol_dir: Path) -> pd.DataFrame:
    frame = pd.read_csv(dataset_csv, dtype={"mol_id": str})
    required = {"mol_id", "barrier", *DESCRIPTOR_COLUMNS}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise KeyError(f"Input CSV missing columns: {missing}")
    frame = frame[["mol_id", "barrier", *DESCRIPTOR_COLUMNS]].copy()
    frame["mol_id"] = frame["mol_id"].map(normalize_mol_id)
    frame["sample_key"] = frame["mol_id"].str.extract(r"(\d{8})", expand=False)
    if frame["sample_key"].isna().any():
        bad = frame.loc[frame["sample_key"].isna(), "mol_id"].head(5).tolist()
        raise RuntimeError(f"Failed to extract 8-digit sample keys. Examples: {bad}")
    frame["barrier"] = pd.to_numeric(frame["barrier"], errors="coerce")
    for column in DESCRIPTOR_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["mol_id", "barrier", *DESCRIPTOR_COLUMNS])
    frame = frame.drop_duplicates(subset=["mol_id"], keep="first").reset_index(drop=True)
    frame["mol_path"] = frame["mol_id"].map(lambda mol_id: str(mol_dir / f"{mol_id}.mol"))
    missing_mol = [path for path in frame["mol_path"].tolist() if not Path(path).exists()]
    if missing_mol:
        raise RuntimeError(f"MOL files are missing: count={len(missing_mol)} first={missing_mol[:3]}")
    return frame


def load_atom_feature_store(path: Path) -> AtomFeatureStore:
    with np.load(path) as archive:
        feature_names = [str(name) for name in archive["feature_names"].tolist()]
        index_by_name = {name: idx for idx, name in enumerate(feature_names)}
        missing = [name for name in ATOM_FEATURE_COLUMNS if name not in index_by_name]
        if missing:
            raise ValueError(f"Atom feature cache missing columns: {missing}")
        selected = [index_by_name[name] for name in ATOM_FEATURE_COLUMNS]
        return AtomFeatureStore(
            sample_keys=archive["sample_keys"].astype(str),
            atom_offsets=archive["atom_offsets"].astype(np.int64),
            atom_numbers=archive["atom_numbers"].astype(np.int64),
            atom_features=archive["atom_features"][:, selected].astype(np.float32),
            feature_names=list(ATOM_FEATURE_COLUMNS),
        )


def apply_descriptor_stats(frame: pd.DataFrame, fold_config: dict[str, list[float]]) -> pd.DataFrame:
    out = frame.copy()
    values = (
        out[DESCRIPTOR_COLUMNS]
        .apply(pd.to_numeric, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
    )
    means = pd.Series(fold_config["descriptor_means"], index=DESCRIPTOR_COLUMNS, dtype=float)
    stds = pd.Series(fold_config["descriptor_stds"], index=DESCRIPTOR_COLUMNS, dtype=float).replace(0.0, 1.0)
    out[DESCRIPTOR_COLUMNS] = ((values.fillna(means) - means) / stds).astype(np.float32)
    return out


def mol_to_data(
    mol_id: str,
    barrier: float,
    mol_path: Path,
    global_features: np.ndarray,
    atom_features: np.ndarray,
) -> Data:
    mol = Chem.MolFromMolFile(str(mol_path), removeHs=False, sanitize=True)
    if mol is None:
        mol = Chem.MolFromMolFile(str(mol_path), removeHs=False, sanitize=False)
    if mol is None:
        raise ValueError(f"Failed to parse MOL file: {mol_path}")
    conf = mol.GetConformer()
    if conf is None:
        raise ValueError(f"No conformer found in MOL file: {mol_path}")
    data = Data(
        z=torch.tensor([atom.GetAtomicNum() for atom in mol.GetAtoms()], dtype=torch.long),
        pos=torch.tensor(conf.GetPositions(), dtype=torch.float32),
        y=torch.tensor([float(barrier)], dtype=torch.float32),
        mol_id=str(mol_id),
    )
    data.global_features = torch.tensor(global_features, dtype=torch.float32)
    data.atom_features = torch.tensor(atom_features, dtype=torch.float32)
    return data


def build_dataset(
    frame: pd.DataFrame,
    atom_feature_store: AtomFeatureStore,
    atom_feature_stats: AtomFeatureStats,
) -> DatasetBuildResult:
    dataset: list[Data] = []
    parse_failures: list[str] = []
    cache_missing = 0
    alignment_failures = 0
    feature_matrix = frame[DESCRIPTOR_COLUMNS].to_numpy(dtype=np.float32, copy=False)
    for index, row in enumerate(frame.itertuples(index=False)):
        sample = atom_feature_store.get_sample(str(row.sample_key))
        if sample is None:
            cache_missing += 1
            continue
        atom_numbers, atom_features_raw = sample
        atom_features = ((atom_features_raw - atom_feature_stats.means) / atom_feature_stats.stds).astype(
            np.float32,
            copy=False,
        )
        try:
            data = mol_to_data(
                mol_id=str(row.mol_id),
                barrier=float(row.barrier),
                mol_path=Path(row.mol_path),
                global_features=feature_matrix[index],
                atom_features=atom_features,
            )
            mol_atomic_numbers = data.z.detach().cpu().numpy().astype(np.int64, copy=False)
            if len(atom_numbers) != int(data.z.numel()) or not np.array_equal(mol_atomic_numbers, atom_numbers):
                alignment_failures += 1
                continue
            dataset.append(data)
        except Exception as exc:
            parse_failures.append(f"{row.mol_id}: {exc}")
    if not dataset:
        raise RuntimeError("No usable molecules remained after parsing and feature alignment.")
    return DatasetBuildResult(
        dataset=dataset,
        parse_failures=parse_failures,
        cache_missing=cache_missing,
        alignment_failures=alignment_failures,
        total_rows=int(len(frame)),
    )


def compute_metrics(y_true: Iterable[float], y_pred: Iterable[float]) -> dict[str, float]:
    y_true_arr = np.asarray(list(y_true), dtype=float)
    y_pred_arr = np.asarray(list(y_pred), dtype=float)
    rmse = math.sqrt(mean_squared_error(y_true_arr, y_pred_arr))
    return {
        "r2": float(r2_score(y_true_arr, y_pred_arr)),
        "rmse": float(rmse),
        "mae": float(mean_absolute_error(y_true_arr, y_pred_arr)),
    }


def load_state_dict(path: Path, device: torch.device) -> dict[str, torch.Tensor]:
    try:
        return torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=device)


def predict_fold(
    fold_index: int,
    eval_rows: pd.DataFrame,
    model_root: Path,
    atom_feature_store: AtomFeatureStore,
    device: torch.device,
    batch_size: int,
) -> FoldPrediction:
    fold_config = FOLD_CONFIGS[int(fold_index)]
    scaled_frame = apply_descriptor_stats(eval_rows, fold_config)
    atom_stats = AtomFeatureStats(
        means=np.asarray(fold_config["atom_feature_means"], dtype=np.float32),
        stds=np.asarray(fold_config["atom_feature_stds"], dtype=np.float32),
    )
    dataset_build = build_dataset(scaled_frame, atom_feature_store, atom_stats)
    model = SchNetFusionRegressor().to(device)
    state_dict = load_state_dict(model_root / f"fold_{fold_index}" / "best_model.pt", device)
    model.load_state_dict(state_dict, strict=True)
    model.eval()

    loader = DataLoader(dataset_build.dataset, batch_size=batch_size, shuffle=False)
    all_ids: list[str] = []
    all_true: list[float] = []
    all_pred: list[float] = []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            pred = model(batch).view(-1)
            all_ids.extend([str(item) for item in batch.mol_id])
            all_true.extend(batch.y.view(-1).detach().cpu().tolist())
            all_pred.extend(pred.detach().cpu().tolist())

    pred_df = pd.DataFrame(
        {
            "mol_id": all_ids,
            "barrier_true": np.asarray(all_true, dtype=float),
            "barrier_pred": np.asarray(all_pred, dtype=float),
        }
    )
    pred_df["signed_error"] = pred_df["barrier_pred"] - pred_df["barrier_true"]
    pred_df["abs_error"] = pred_df["signed_error"].abs()
    metrics = compute_metrics(all_true, all_pred)
    metrics.update(
        {
            "fold_index": int(fold_index),
            "n_input_rows": int(len(eval_rows)),
            "n_usable_rows": int(dataset_build.usable_rows),
        }
    )
    if dataset_build.parse_failures:
        print(f"fold={fold_index} skipped_parse_failures={len(dataset_build.parse_failures)}")
    if dataset_build.cache_missing or dataset_build.alignment_failures:
        print(
            f"fold={fold_index} cache_missing={dataset_build.cache_missing} "
            f"alignment_failures={dataset_build.alignment_failures}"
        )
    return FoldPrediction(fold_index=int(fold_index), metrics=metrics, predictions=pred_df)


def merge_ensemble(predictions: list[FoldPrediction]) -> tuple[pd.DataFrame, dict[str, float | int]]:
    merged: pd.DataFrame | None = None
    for item in predictions:
        pred = item.predictions[["mol_id", "barrier_true", "barrier_pred"]].rename(
            columns={"barrier_pred": f"barrier_pred_fold_{item.fold_index}"}
        )
        if merged is None:
            merged = pred
        else:
            merged = merged.merge(pred, on=["mol_id", "barrier_true"], how="inner", validate="one_to_one")
    if merged is None or merged.empty:
        raise RuntimeError("No fold predictions were available.")
    pred_cols = [col for col in merged.columns if col.startswith("barrier_pred_fold_")]
    merged["barrier_pred_ensemble"] = merged[pred_cols].to_numpy(dtype=float).mean(axis=1)
    merged["signed_error"] = merged["barrier_pred_ensemble"] - merged["barrier_true"]
    merged["abs_error"] = merged["signed_error"].abs()
    metrics = compute_metrics(merged["barrier_true"], merged["barrier_pred_ensemble"])
    summary: dict[str, float | int] = {
        "n_samples": int(len(merged)),
        "n_folds": int(len(predictions)),
        **metrics,
    }
    return merged.sort_values("abs_error", ascending=False).reset_index(drop=True), summary


def main() -> int:
    args = parse_args()
    device = resolve_device(args.device)
    dataset_csv = resolve_package_path(args.dataset_csv, PACKAGE_ROOT / "dataset" / "test_inputs.csv")
    mol_dir = resolve_package_path(args.mol_dir, PACKAGE_ROOT / "dataset" / "mol_files")
    feature_cache = resolve_package_path(
        args.atom_feature_cache,
        PACKAGE_ROOT / "dataset" / "features" / "barrier_atom_features_basic.npz",
    )
    model_root = resolve_package_path(args.model_root, PACKAGE_ROOT / "model")

    eval_rows = load_eval_rows(dataset_csv, mol_dir)
    atom_feature_store = load_atom_feature_store(feature_cache)

    if args.mode == "per_fold":
        fold_indices = [int(args.fold_index)]
    else:
        fold_indices = sorted(FOLD_CONFIGS)

    fold_outputs = [
        predict_fold(
            fold_index=fold_index,
            eval_rows=eval_rows,
            model_root=model_root,
            atom_feature_store=atom_feature_store,
            device=device,
            batch_size=int(args.batch_size),
        )
        for fold_index in fold_indices
    ]

    if args.mode == "per_fold":
        result = fold_outputs[0]
        output_df = result.predictions.sort_values("abs_error", ascending=False).reset_index(drop=True)
        summary = result.metrics
        print(
            f"fold={result.fold_index} split=test "
            f"r2={float(summary['r2']):.6f} "
            f"rmse={float(summary['rmse']):.6f} "
            f"mae={float(summary['mae']):.6f}"
        )
    else:
        output_df, summary = merge_ensemble(fold_outputs)
        print(
            "ensemble split=test "
            f"r2={float(summary['r2']):.6f} "
            f"rmse={float(summary['rmse']):.6f} "
            f"mae={float(summary['mae']):.6f}"
        )

    if args.output_csv:
        output_path = resolve_package_path(args.output_csv, PACKAGE_ROOT / "predictions.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_df.to_csv(output_path, index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
