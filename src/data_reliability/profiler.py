from __future__ import annotations

from pathlib import Path

import pandas as pd

from .models import DatasetProfile


def load_table(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    if source.suffix.lower() != ".csv":
        raise ValueError("Day 1 supports CSV input only")
    return pd.read_csv(source)


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

