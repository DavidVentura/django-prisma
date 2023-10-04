from django.db.models.sql.compiler import (
    SQLAggregateCompiler as BaseSQLAggregateCompiler,
    SQLCompiler as BaseSQLCompiler,
    SQLDeleteCompiler as BaseSQLDeleteCompiler,
    SQLInsertCompiler as BaseSQLInsertCompiler,
    SQLUpdateCompiler as BaseSQLUpdateCompiler,
)


class SQLCompiler(BaseSQLCompiler):
    pass


class SQLInsertCompiler(BaseSQLInsertCompiler, SQLCompiler):
    """A wrapper class for compatibility with Django specifications."""

    pass


class SQLDeleteCompiler(BaseSQLDeleteCompiler, SQLCompiler):
    """A wrapper class for compatibility with Django specifications."""

    pass


class SQLUpdateCompiler(BaseSQLUpdateCompiler, SQLCompiler):
    """A wrapper class for compatibility with Django specifications."""

    pass


class SQLAggregateCompiler(BaseSQLAggregateCompiler, SQLCompiler):
    """A wrapper class for compatibility with Django specifications."""

    pass
