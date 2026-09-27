"""Target-date splits with common evaluation dates for every sequence length."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


@dataclass
class SplitPlan:
    target_positions: np.ndarray
    train_end: int
    validation_end: int

    def slices(self):
        return {"train": slice(0, self.train_end),
                "validation": slice(self.train_end, self.validation_end),
                "test": slice(self.validation_end, len(self.target_positions))}


def make_plan(frame, config):
    # Filtered warm-up rows must not turn a multi-session gap into a one-session target.
    max_length = max(config["sequence_lengths"])
    targets = np.arange(max_length, len(frame))
    if "session_number" in frame:
        numbers = frame["session_number"].to_numpy()
        targets = np.array([t for t in targets if np.all(np.diff(numbers[t - max_length:t + 1]) == 1)], dtype=int)
    count = len(targets)
    train_end = int(count * config["train_fraction"])
    validation_end = train_end + int(count * config["validation_fraction"])
    if min(train_end, validation_end - train_end, count - validation_end) < 20:
        raise ValueError("Insufficient samples: each chronological split needs at least 20 targets")
    return SplitPlan(targets, train_end, validation_end)


def prepare(frame, feature_names, length, plan):
    positions = plan.target_positions
    if length > positions.min():
        raise ValueError("Sequence length exceeds available context")
    values = frame[feature_names].to_numpy(dtype=float)
    labels = frame[["adj_official_close"]].to_numpy(dtype=float)
    train_targets = positions[:plan.train_end]
    # Fit only rows actually used by training inputs; no validation/test targets or inputs.
    input_positions = np.unique(np.concatenate([np.arange(t - length, t) for t in train_targets]))
    x_scaler = StandardScaler().fit(values[input_positions])
    y_scaler = StandardScaler().fit(labels[train_targets])
    scaled = x_scaler.transform(values)
    x = np.stack([scaled[t - length:t] for t in positions]).astype("float32")
    y = y_scaler.transform(labels[positions]).astype("float32")
    dates = pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d").to_numpy()[positions]
    previous = labels[positions - 1, 0]
    splits = {}
    for name, cut in plan.slices().items():
        splits[name] = {"X": x[cut], "y": y[cut], "dates": dates[cut],
                        "actual": labels[positions[cut], 0], "persistence": previous[cut],
                        "target_positions": positions[cut]}
    return splits, x_scaler, y_scaler

