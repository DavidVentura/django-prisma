
from typing import Any, Protocol, Optional

from django.db.models.query import Field
from django.db.models.sql.constants import MULTI, SINGLE
from django.db.models.sql.compiler import (
    SQLAggregateCompiler as BaseSQLAggregateCompiler,
    SQLCompiler as BaseSQLCompiler,
    SQLDeleteCompiler as BaseSQLDeleteCompiler,
    SQLInsertCompiler as BaseSQLInsertCompiler,
    SQLUpdateCompiler as BaseSQLUpdateCompiler,
)
from django.db.models.sql.datastructures import Join
from django.db.models.sql.where import WhereNode, AND, tree
from django.db.models.lookups import Exact, In
from django.db.models.expressions import Col

from django_prisma.manager import CacheableManager, CacheStrategy

class Statement(Protocol):
    statement: dict
    cache_strategy: Optional[CacheStrategy]
    def dict_to_tuple(self, data: dict[str, Any]) -> tuple[Any]:
        ...

class InsertStatement(Statement):
    def __init__(self, model: str, field_names: list[Field], values: list):
        self.model = model
        self.field_names = [str(f.name) for f in field_names]
        self.field_values = values
        self.cache_strategy = None

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

    def dict_to_tuple(self, data: dict[str, Any]) -> list[Any]:
        ret = [data[colname] for colname in self.field_names]
        return ret


def node_to_dict(n: tree.Node):
    match n:
        case Exact():
            return {n.lhs.field.name: n.rhs}
        case WhereNode():
            return where_to_dict(n)
        case In():
            assert isinstance(n.lhs, Col)
            assert isinstance(n.rhs, list)
            return {n.lhs.field.name: {"in": n.rhs}}
    assert False, f'got {n}'


def where_to_dict(w: WhereNode):
    ret = {}
    if w.connector == AND:
        for c in w.children:
            ret.update(node_to_dict(c))
    return ret


class SelectStatement(Statement):
    def __init__(self, model: str, field_names: list[str], where: WhereNode, joins: list[Join], cache_strategy: Optional[CacheStrategy]):
        self.model = model
        self.field_names = field_names
        self.where = where
        self.joins = joins
        self.cache_strategy = cache_strategy
        _where = where_to_dict(where)
        self.statement = {
            "modelName": model,
            "action": "findMany",
            "query": {
                "arguments": {
                    "where": _where,
                },
                "selection": {"$composites": True, "$scalars": True},
            },
        }

        for join in joins:
            # True here means all of them in default order
            # Can apply sorting and filtering
            # This is recursive also
            # And can select a subset of fields.. but not sure how to in django
            self.statement['query']['selection'][join.join_field.name] = True

    def query(self) -> dict[str, Any]:
        return self.statement

    def dict_to_tuple(self, data: dict[str, Any]) -> list[Any]:
        ret = [data[colname] for colname in self.field_names]
        for join in self.joins:
            jname = join.join_field.name
            join_values = data[jname].values()  # order?
            ret.extend(join_values)
        return ret


class UpdateStatement(Statement):
    def __init__(self, model: str, field_name_values: dict[str, Any], where: WhereNode, joins: list[Join], cache_strategy: Optional[CacheStrategy]):
        self.model = model
        self.where = where
        self.joins = joins
        self.cache_strategy = None
        _where = where_to_dict(where)
        self.statement = {
            "modelName": model,
            "action": "updateMany",
            "query": {
                "arguments": {
                    "where": _where,
                    "data": field_name_values,
                },
                "selection": {"$composites": True, "$scalars": True},
            },
        }
        print(self.statement)

    def dict_to_tuple(self, data: dict[str, Any]) -> list[Any]:
        return [data['count']]

class SelectSQLCompiler(BaseSQLCompiler):
    def __init__(self, query, connection, using, elide_empty=True):
        super().__init__(query, connection, using, elide_empty)

    def as_sql(self):
        # i think only sql.InsertQuery.__str__ calls as_sql
        raise ValueError("somebody still calls as_sql")

    def executable(self):
        # pre_sql_setup mutates self and populates `self.select`
        extra_select, order_by, group_by = self.pre_sql_setup(with_col_aliases=False)
        opts = self.query.get_meta()
        # any way to find the actual manager/queryset? then i can pass the cache parameters
        # now i could check in opts.managers whether there's a CachableQueryset, but that
        # does not tell me whether the manager was _used_ only whether the model has it _defined_.
        fields = [(f.db_column or f.attname) for f in opts.fields]

        joins = []
        for alias_name, alias in self.query.alias_map.items():
            if not self.query.alias_refcount[alias_name]:
                continue
            if not isinstance(alias, Join):
                # i guess?
                continue
            joins.append(alias)
        cache_strategy = None
        for m in opts.managers:
            if isinstance(m, CacheableManager):
                cache_strategy = m.cache_strategy
        st = SelectStatement(opts.db_table, fields, self.where, joins, cache_strategy)
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


class SQLInsertCompiler(SelectSQLCompiler, BaseSQLInsertCompiler):
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


class SQLDeleteCompiler(SelectSQLCompiler, BaseSQLDeleteCompiler):
    """A wrapper class for compatibility with Django specifications."""

    pass


class SQLUpdateCompiler(SelectSQLCompiler, BaseSQLUpdateCompiler):
    """A wrapper class for compatibility with Django specifications."""
    def executable(self):
        new_values = {}
        opts = self.query.get_meta()
        for field, model, val in self.query.values:
            val = field.get_db_prep_save(val, connection=self.connection)
            new_values[field.name] = val
        print(self.query.where, new_values)
        return UpdateStatement(opts.db_table, new_values, self.query.where, [], None)


class SQLAggregateCompiler(SelectSQLCompiler, BaseSQLAggregateCompiler):
    """A wrapper class for compatibility with Django specifications."""

    pass


SQLCompiler = SelectSQLCompiler
