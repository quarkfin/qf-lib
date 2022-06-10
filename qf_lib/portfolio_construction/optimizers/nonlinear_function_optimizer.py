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

from typing import Callable, Sequence, Union, Tuple, List

import numpy as np
import scipy.optimize

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class NonlinearFunctionOptimizer:
    """
    Class used for optimizing nonlinear problems.
    """

    @classmethod
    def get_weights(cls, minimised_func: Callable[[Sequence[float]], float], num_of_assets: int,
                    upper_constraints: Union[float, Sequence[float]], max_iter: int = 10000) -> np.ndarray:
        one_over_n_weights = np.array([1 / num_of_assets] * num_of_assets)
        bounds = cls._get_bounds(num_of_assets, upper_constraints)

        def weights_sum_to_one_fun(weights):
            result = weights.sum() - 1.0
            return result

        weights_sum_up_to_one_constr = {
            'type': 'eq',
            'fun': weights_sum_to_one_fun
        }

        options = {
            'disp': False,
            'maxiter': max_iter
        }

        optimization_result = scipy.optimize.minimize(
            fun=minimised_func, method='SLSQP', x0=one_over_n_weights, bounds=bounds,
            constraints=weights_sum_up_to_one_constr, options=options)
        logger = qf_logger.getChild(cls.__name__)
        if optimization_result.success:
            logger.info(optimization_result.message)
        else:
            logger.warning("Unsuccessful optimization: " + optimization_result.message)

        return optimization_result.x

    @classmethod
    def _get_bounds(cls, num_of_assets: int, upper_constraints: Union[Sequence[float], float]) \
            -> List[Tuple[float, float]]:
        zeros = np.array([0] * num_of_assets)
        if isinstance(upper_constraints, Sequence):
            assert len(upper_constraints) == num_of_assets
        else:
            upper_constraints = [upper_constraints] * num_of_assets

        return list(zip(zeros, upper_constraints))
