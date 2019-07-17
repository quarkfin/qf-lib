from typing import List


def generate_sample_column_names(num_of_columns: int) -> List[str]:
    """
    Generates columns' names like a, b, c, ...
    """
    regressors_names = []
    for i in range(ord('a'), ord('a') + num_of_columns):
        regressors_names.append(chr(i))

    return regressors_names
