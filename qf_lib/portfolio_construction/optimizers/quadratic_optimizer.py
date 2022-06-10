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

from typing import Union, Sequence

import numpy as np
from cvxopt import matrix
from cvxopt import solvers

import qf_lib.portfolio_construction.optimizers.helpers.quadratic_constraints_helpers as constr


class QuadraticOptimizer:
    """
    Class used for optimizing quadratic problems.
    """
    options = {
        'show_progress': False,
        'abstol': 1e-15,
        'reltol': 1e-15,
        'feastol': 1e-15,
        'maxiters': 1000
    }

    @classmethod
    def get_optimal_weights(cls, P: np.ndarray = None, q: np.ndarray = None,
                            upper_constraints: Union[Sequence, float] = None) -> np.ndarray:
        """
        Solves the problem defined by matrix h, vector f and constraints.

        Parameters
        ----------
        P
            a square matrix from the quadratic formula
        q
            a vector (can be empty) from the quadratic formula
        upper_constraints
            vector of upper limits of weights (if it's a single value, the constraint will be the same for each weight).
            Example: 0.5 means that max allocation of some asset can be 50%.

        Returns
        -------
        weights
            best weights for the given problem. Sum of all weights is equal 1.
        """
        assets_number = P.shape[0]
        if P is not None:
            P = matrix(P)
        else:
            P = matrix(0.0, (assets_number, assets_number))

        if q is not None:
            q = matrix(q)
        else:
            q = matrix(0.0, (assets_number, 1))

        A, b = constr.sum_weights_equal_1_constraint(assets_number)
        G, h = constr.each_weight_greater_than_0_constraint(assets_number)

        if upper_constraints is not None:
            G_2, h_2 = constr.upper_bound_constraint(assets_number, upper_constraints)
            G, h = constr.merge_constraints(G, h, G_2, h_2)

        initial_weights = matrix(1.0 / assets_number, (assets_number, 1))

        # minimize (1/2)x'Px + q'x
        # subject to Gx <= h; Ax = b
        result = solvers.qp(P, q, G, h, A, b, initvals=initial_weights, options=cls.options)
        return np.array(result['x']).squeeze()
