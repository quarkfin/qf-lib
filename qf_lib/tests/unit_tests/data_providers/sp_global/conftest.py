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
import pytest
from sqlalchemy.ext.automap import automap_base

from qf_lib.tests.helpers.test_db_connection_provider import TestDBConnectionProvider


@pytest.fixture
def db_conn_provider():
    return TestDBConnectionProvider()


@pytest.fixture
def initialize_database(db_conn_provider):
    from qf_lib.tests.unit_tests.data_providers.sp_global.init_db import initialize_database
    # Initialize the database schema
    with db_conn_provider.engine.connect() as conn:
        initialize_database(db_conn_provider.engine)
        yield


@pytest.fixture
def Base(db_conn_provider, initialize_database):
    Base = automap_base()
    Base.prepare(db_conn_provider.engine, reflect=True)
    return Base


@pytest.fixture
def session(db_conn_provider):
    session = db_conn_provider.Session()
    yield session
    session.close()
