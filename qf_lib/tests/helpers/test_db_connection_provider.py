from sqlalchemy import create_engine

from data_providers.db_connection_providers import DBConnectionProvider


class TestDBConnectionProvider(DBConnectionProvider):
    def __init__(self):
        super().__init__(None)

    def _create_engine(self, settings, **kwargs):
        return create_engine(r"sqlite:///:memory:")
