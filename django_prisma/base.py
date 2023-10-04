from django.db.backends.base.creation import BaseDatabaseCreation
from django.db.backends.base.client import BaseDatabaseClient
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.base.introspection import BaseDatabaseIntrospection

class PrismaDatabaseFeatures:
    def __init__(self, wrapper):
        self.wrapper = wrapper

class PrismaDatabaseOperations(BaseDatabaseOperations):
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.compiler_module = "django_prisma.compiler"

class PrismaDatabaseClient(BaseDatabaseClient):
    def __init__(self, wrapper):
        self.wrapper = wrapper

class PrismaDatabaseIntrospection(BaseDatabaseIntrospection):
    def __init__(self, wrapper):
        self.wrapper = wrapper

    def get_table_list(self, cursor):
        return []

class PrismaDatabaseCreation(BaseDatabaseCreation):
    pass

class Error(Exception):
    pass
class DatabaseError(Error):
    pass
class DataError(DatabaseError):
    pass

class PrismaDatabase:
    DataError = DataError
    OperationalError = Error
    IntegrityError = Error
    InternalError = Error
    ProgrammingError = Error
    NotSupportedError = Error
    DatabaseError = Error
    InternalError = Error
    InterfaceError = Error
    Error = Error

class Cursor:
    def close(self):
        pass

def complain(*args, **kwargs):
    raise ImproperlyConfigured(
        "settings.DATABASES is improperly configured. "
        "Please supply the ENGINE value. Check "
        "settings documentation for more details."
    )


def ignore(*args, **kwargs):
    pass

class PrismaDatabaseWrapper(BaseDatabaseWrapper):
    vendor = 'Prisma'
    Database = PrismaDatabase

    client_class = PrismaDatabaseClient
    creation_class = PrismaDatabaseCreation
    features_class = PrismaDatabaseFeatures
    introspection_class = PrismaDatabaseIntrospection
    ops_class = PrismaDatabaseOperations

    operators = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_cursor(self, name=None):
        print("cursor")
        return Cursor()

    def is_usable(self):
        return True

    def get_new_connection(self, conn_params):
        print("get new conn")

    def connect(self):
        print("called connect")

DatabaseWrapper = PrismaDatabaseWrapper
