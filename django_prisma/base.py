import base64
import hashlib
import json

import requests
import urllib3

urllib3.disable_warnings()

from django.db.backends.postgresql.features import DatabaseFeatures
from django.db.backends.base.creation import BaseDatabaseCreation
from django.db.backends.base.client import BaseDatabaseClient
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


GRAPHQL_ENDPOINT = "https://accelerate.prisma-data.net/5.1.1/{schema_id}/graphql"
SCHEMA_ENDPOINT = "https://accelerate.prisma-data.net/5.1.1/{schema_id}/schema"


class PrismaDatabaseFeatures(DatabaseFeatures):
    pass


class PrismaDatabaseOperations(BaseDatabaseOperations):
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.compiler_module = "django_prisma.compiler"
        super().__init__(wrapper)

    def quote_name(self, name):
        return f'"{name}"'

    def bulk_insert_sql(self, fields, placeholder_rows):
        print("bulk", fields, placeholder_rows)
        return ""


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
    def __init__(self, session, schema_id):
        self.session = session
        self.schema_id = schema_id

    def execute(self, other, other2=None):
        key = other.statement["action"] + other.statement["modelName"]  # findMany User
        data = json.dumps(other.statement)
        r = self.session.post(GRAPHQL_ENDPOINT.format(schema_id=self.schema_id), verify=False, data=data)
        _json = r.json()
        for error in _json.get("errors", []):
            ufe = error["user_facing_error"]
            if ufe["error_code"] == "P2002":
                raise PrismaDatabase.IntegrityError(ufe["message"])

        result = r.json()["data"][key]
        if isinstance(result, list):
            return [[[r[colname] for colname in other.field_names] for r in result]]
        return [[[result[colname] for colname in other.field_names]]]

    def close(self):
        pass


class DatabaseSchemaEditor(BaseDatabaseSchemaEditor):
    pass


class PrismaDatabaseWrapper(BaseDatabaseWrapper):
    vendor = "Prisma"
    Database = PrismaDatabase

    client_class = PrismaDatabaseClient
    creation_class = PrismaDatabaseCreation
    features_class = PrismaDatabaseFeatures
    introspection_class = PrismaDatabaseIntrospection
    ops_class = PrismaDatabaseOperations
    SchemaEditorClass = DatabaseSchemaEditor

    operators = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open(self.settings_dict["SCHEMA_PATH"], "rb") as fd:
            self.schema = fd.read()
        self.schema_inline = base64.b64encode(self.schema)
        self.schema_id = hashlib.sha256(self.schema_inline).hexdigest()
        self.token = self.settings_dict["TOKEN"]

        headers = {"Connection": "keep-alive", "Authorization": f"Bearer {self.token}"}
        self.session = requests.Session()
        self.session.headers.update(headers)
        self._started = False

    def create_cursor(self, name=None):
        return Cursor(self.session, self.schema_id)

    def is_usable(self):
        return self._started

    def get_new_connection(self, conn_params):
        print("get new conn")

    def connect(self):
        print("called connect")
        if self._started:
            return
        r = self.session.put(SCHEMA_ENDPOINT.format(schema_id=self.schema_id), data=self.schema_inline, verify=False)
        if not r.ok:
            raise ValueError(f"Failed to start up data-proxy: {r.text}")
        self._started = True


DatabaseWrapper = PrismaDatabaseWrapper
