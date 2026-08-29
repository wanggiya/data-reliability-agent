from __future__ import annotations

from pathlib import Path

import pandas as pd

from .models import DatasetProfile


def load_table(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(source)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(source)
    if suffix == ".json":
        return pd.read_json(source)
    if suffix == ".parquet":
        return pd.read_parquet(source)
    raise ValueError("Supported inputs: CSV, Excel, JSON records, and Parquet")


def write_table(frame: pd.DataFrame, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = target.suffix.lower()
    if suffix == ".csv":
        frame.to_csv(target, index=False)
    elif suffix in {".xlsx", ".xls"}:
        frame.to_excel(target, index=False)
    elif suffix == ".json":
        frame.to_json(target, orient="records", indent=2, date_format="iso")
    elif suffix == ".parquet":
        frame.to_parquet(target, index=False)
    else:
        raise ValueError("Output extension must be CSV, Excel, JSON, or Parquet")
    return target


def profile_dataset(path: str | Path) -> tuple[pd.DataFrame, DatasetProfile]:
    frame = load_table(path)
    numeric = frame.select_dtypes(include="number").columns.tolist()
    lowered = {column: column.lower() for column in frame.columns}
    date_candidates = [c for c, low in lowered.items() if "date" in low or "month" in low or "year" in low]
    id_candidates = [c for c, low in lowered.items() if low == "id" or low.endswith("_id") or low.endswith("id")]
    sample = frame.head(5).where(pd.notna(frame.head(5)), None).to_dict(orient="records")
    profile = DatasetProfile(
        path=str(Path(path)),
        rows=len(frame),
        columns=len(frame.columns),
        column_names=frame.columns.tolist(),
        dtypes={c: str(t) for c, t in frame.dtypes.items()},
        null_counts={c: int(v) for c, v in frame.isna().sum().items()},
        sample=sample,
        numeric_columns=numeric,
        date_candidates=date_candidates,
        id_candidates=id_candidates,
    )
    return frame, profile
