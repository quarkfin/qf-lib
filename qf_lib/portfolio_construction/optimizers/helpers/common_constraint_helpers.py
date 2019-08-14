#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from typing import Optional, Union, Sequence

import numpy as np

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


def prepare_upper_bounds_vector(
        assets_number: int, upper_constraints: Union[float, Sequence[float]]) -> Optional[np.ndarray]:
    if upper_constraints is None:
        return None
    elif isinstance(upper_constraints, float):
        upper_constraints = np.array([upper_constraints] * assets_number)

    return upper_constraints


def put_weights_below_constraint(weights: np.ndarray, upper_constraints: np.ndarray, max_iter: int = 1000,
                                 epsilon: float = 0.00001) -> np.ndarray:
    """
    Takes a vector of weights and a vector of upper constraints (both of the same length) and ensures that no weights
    exceed their upper constraints. It is done iteratively by cutting the weights exceeding the upper bound
    and rescaling the weights vector so that the weights sum up to 1.

    Parameters
    ----------
    weights
        vector of weights
    upper_constraints
        vector of upper constraints
    max_iter
        maximal number of iterations done for adjusting the weights vector. If the max_iter number of iterations
        is exceeded, the proper warning is given
    epsilon
        a difference between original weight and a new one which is considered to be equal to no change

    Returns
    -------
    vector of new weights which satisfy their upper bound constraints
    """
    assert upper_constraints.sum() >= 1

    new_weights = weights
    for _ in range(max_iter):
        new_weights, max_difference = _calculate_new_weights(new_weights, upper_constraints)

        if max_difference <= epsilon:
            break
    else:
        logger = qf_logger.getChild(__name__)
        logger.warning("put_weights_below_constraint: \nIt was not possible to find weights within the constraints "
                       "in {:d} iterations".format(max_iter))

    return new_weights


def _calculate_new_weights(weights, upper_constraints):
    new_weights = np.copy(weights)

    indices_above = weights > upper_constraints
    new_weights[indices_above] = upper_constraints[indices_above]

    new_weights /= new_weights.sum()
    max_difference = np.max(new_weights - upper_constraints)

    return new_weights, max_difference
