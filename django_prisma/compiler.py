from typing import Any
from django.db.models.query import Field
from django.db.models.expressions import Col
from django.db.models.sql.constants import MULTI, CURSOR, SINGLE
from django.db.models.sql.compiler import (
    SQLAggregateCompiler as BaseSQLAggregateCompiler,
    SQLCompiler as BaseSQLCompiler,
    SQLDeleteCompiler as BaseSQLDeleteCompiler,
    SQLInsertCompiler as BaseSQLInsertCompiler,
    SQLUpdateCompiler as BaseSQLUpdateCompiler,
)
from django.db.models.sql.where import WhereNode, AND, tree
from django.db.models.lookups import Exact


class InsertStatement:
    def __init__(self, model: str, field_names: list[Field], values: list):
        self.model = model
        self.field_names = [f.name for f in field_names]
        self.field_values = values

    @property
    def statement(self):
        data = dict(zip(self.field_names, self.field_values))
        statement = {
            "modelName": self.model,
            "action": "createOne",
            "query": {"arguments": {"data": data}, "selection": {"$composites": True, "$scalars": True}},
        }
        return statement

    def __mod__(self, field_values):
        self.field_values = field_values()
        return self.statement


def node_to_dict(n: tree.Node):
    match n:
        case Exact():
            return {n.lhs.field.name: n.rhs}
        case WhereNode():
            return where_to_dict(n)
    assert False


def where_to_dict(w: WhereNode):
    ret = {}
    if w.connector == AND:
        for c in w.children:
            ret.update(node_to_dict(c))
    return ret


class SelectStatement:
    def __init__(self, model: str, cols: list[Col], where: WhereNode):
        self.model = model
        self.field_names = [f.field.name for f in cols]
        self.where = where
        _where = where_to_dict(where)
        self.statement = {
            "modelName": "User",
            "action": "findMany",
            "query": {
                "arguments": {
                    "skip": 0,
                    "take": 4,
                    "where": _where,
                },
                "selection": {"$composites": True, "$scalars": True},
            },
        }

    def query(self) -> dict[str, Any]:
        return self.statement


class SQLCompiler(BaseSQLCompiler):
    def __init__(self, query, connection, using, elide_empty=True):
        super().__init__(query, connection, using, elide_empty)

    def as_sql(self):
        # i think only sql.InsertQuery.__str__ calls as_sql
        raise ValueError("somebody still calls as_sql")

    def executable(self):
        # pre_sql_setup mutates self and populates `self.select`
        extra_select, order_by, group_by = self.pre_sql_setup(with_col_aliases=False)
        opts = self.query.get_meta()
        fields = [f[0] for f in self.select]
        st = SelectStatement(opts.db_table, fields, self.where)
        return st

    def field_as_sql(self, field, val):
        raise ValueError()

    def execute_sql(self, result_type=MULTI, chunked_fetch=False, chunk_size=1024):
        q = self.executable()
        c = self.connection.cursor()
        res = c.execute(q)
        if res and result_type == SINGLE:
            assert len(res) == 1
            return res[0]
        return res

    def assemble_as_sql(self, fields, value_rows):
        raise ValueError


class SQLInsertCompiler(SQLCompiler, BaseSQLInsertCompiler):
    """A wrapper class for compatibility with Django specifications."""

    def executable(self):
        opts = self.query.get_meta()
        fields = self.query.fields or [opts.pk]
        assert len(self.query.objs) == 1
        values = [
            [self.prepare_value(field, self.pre_save_val(field, obj)) for field in fields] for obj in self.query.objs
        ]
        values = values[0]
        st = InsertStatement(opts.db_table, fields, values)
        return [st, values]

    def execute_sql(self, returning_fields=None):
        print("retfields", returning_fields)
        with self.connection.cursor() as cursor:
            st, _ = self.executable()
            return cursor.execute(st)
        # this is supposed to apply converters if returning

    pass


class SQLDeleteCompiler(SQLCompiler, BaseSQLDeleteCompiler):
    """A wrapper class for compatibility with Django specifications."""

    pass


class SQLUpdateCompiler(SQLCompiler, BaseSQLUpdateCompiler):
    """A wrapper class for compatibility with Django specifications."""

    pass


class SQLAggregateCompiler(SQLCompiler, BaseSQLAggregateCompiler):
    """A wrapper class for compatibility with Django specifications."""

    pass
