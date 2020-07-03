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

from typing import Union, Sequence, Tuple

from cvxopt import matrix, spmatrix, sparse

from qf_lib.portfolio_construction.optimizers.helpers.common_constraint_helpers import prepare_upper_bounds_vector

"""
In quadratic solvers there are two types of constraints: equality constraints and inequality constraints.

Equality constraints are expressed in the form of: A*x == b, where A is a matrix (so called multiplier)
and b is a vector of values. A*x is a dot product of the multiplier and a vector of weights (which is the result
of the optimization process).

Inequality constraints are expressed as: G*x <= h, where G is a matrix (multiplier) and h is a vector of values.
G*x is a dot product of matrix G and a weights' vector (x).

For more information see: http://cvxopt.org/userguide/coneprog.html
"""


def sum_weights_equal_1_constraint(assets_number: int) -> Tuple[matrix, matrix]:
    """
    Creates a constraint which assures that all weights sum up to 1.
    """
    A = matrix(1.0, (1, assets_number))
    b = matrix(1.0)
    return A, b


def each_weight_greater_than_0_constraint(assets_number: int) -> Tuple[matrix, matrix]:
    """
    Creates a constraint which assures that no weight has a negative value.
    """
    G = spmatrix(-1.0, range(assets_number), range(assets_number))
    h = matrix(0.0, (assets_number, 1))
    return G, h


def upper_bound_constraint(assets_number: int, upper_constraints: Union[float, Sequence[float]]) \
        -> Tuple[matrix, matrix]:
    """
    Creates a constraint which assures that no weight exceeds its upper bound value.
    """
    upper_constraints = prepare_upper_bounds_vector(assets_number, upper_constraints)
    upper_constraints = matrix(upper_constraints)

    G = spmatrix(1.0, range(assets_number), range(assets_number))
    h = matrix(upper_constraints)

    return G, h


def merge_constraints(multiplier_1: matrix, constr_values_1: matrix, multiplier_2: matrix, constr_values_2: matrix) \
        -> Tuple[matrix, matrix]:
    """
    Combines two constraints into one constraint.
    """
    multiplier = sparse([[multiplier_1, multiplier_2]])
    constr_values = matrix([[constr_values_1, constr_values_2]])

    return multiplier, constr_values
