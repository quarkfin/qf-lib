from typing import Sequence, Any


def rolling_window_slices(index: Sequence[Any], size: Any, step: int=1) -> Sequence[slice]:
    slices = []
    last_idx_value = index[-1]

    start_indices = [idx for i, idx in enumerate(index) if i % step == 0]

    for idx in start_indices:
        start_idx = idx
        end_idx = start_idx + size

        if end_idx < last_idx_value:
            slices.append(slice(start_idx, end_idx))
        else:
            slices.append(slice(start_idx, last_idx_value))
            break

    return slices
