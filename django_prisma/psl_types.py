import dataclasses

from typing import Optional


@dataclasses.dataclass
class PSLFK:
    pass


@dataclasses.dataclass
class PSLType:
    pass


@dataclasses.dataclass
class UserDefinedType(PSLType):
    name: str


@dataclasses.dataclass
class Int(PSLType):
    pass


@dataclasses.dataclass
class String(PSLType):
    pass


@dataclasses.dataclass
class Attribute:
    pass


@dataclasses.dataclass
class AttributePK(Attribute):
    pass


@dataclasses.dataclass
class AttributeUnique(Attribute):
    pass


@dataclasses.dataclass
class AttributeArray(Attribute):
    pass


@dataclasses.dataclass
class AttributeDefaultAutoinc(Attribute):
    pass


@dataclasses.dataclass
class AttributeRelation(Attribute):
    local_field_name: list[str]
    remote_field_name: list[str]


@dataclasses.dataclass
class PSLColumn:
    name: str
    type_: Int | String | UserDefinedType
    props: list[Attribute]
    is_array: bool
    is_opt: bool

    @property
    def django_type(self) -> str:
        match self.type_:
            case Int():
                if AttributeDefaultAutoinc() in self.props:
                    return "models.AutoField"
                return f"models.IntegerField"
            case String():
                return f"models.CharField"
            case UserDefinedType(_):
                return "models.ForeignKey"

    @property
    def django_field_props(self) -> str:
        props = []
        for p in self.props:
            match p:
                case AttributeDefaultAutoinc():
                    continue
                case AttributePK():
                    props.append("primary_key=True")
                case AttributeUnique():
                    props.append("unique=True")
                case AttributeRelation(_):
                    props.append(f'to={self.type_.name}')
                    props.append('on_delete=models.CASCADE')
                    props.append(f'db_column="{p.local_field_name[0]}"')
                case _:
                    assert False, p

        if self.is_opt:
            props.append("null=True")

        return ", ".join(props)

    def to_django_model(self) -> str:
        return f"{self.name} = {self.django_type}({self.django_field_props})"

    @property
    def represent_in_django(self) -> bool:
        if isinstance(self.type_, UserDefinedType) and self.is_array:
            # This is the back-reference / "reverse" to a foreign key
            return False
        return True


@dataclasses.dataclass
class CompoundUniqueConstraint:
    fields: list[str]


@dataclasses.dataclass
class PSLModel:
    name: str
    columns: list[PSLColumn]
    compound_unique_constraints: list[CompoundUniqueConstraint]

    def _columns_to_represent_in_django(self) -> list[PSLColumn]:
        columns = [c for c in self.columns if c.represent_in_django]
        usdt_local_name = []
        for c in columns:
            if not isinstance(c.type_, UserDefinedType):
                continue
            usdt_local_name.extend([p.local_field_name for p in c.props if isinstance(p, AttributeRelation)])

        usdt_local_name = [item for sublist in usdt_local_name for item in sublist]
        return [c for c in columns if c.name not in usdt_local_name]

    def to_django_model(self) -> str:
        # Filter columns whose name match another column of type UserDefinedType.local_field_name
        _fields = [column.to_django_model() for column in self._columns_to_represent_in_django()]
        str_fields = [f"    {f}" for f in _fields]
        fields = "\n".join(str_fields)

        return f"""
class {self.name}(models.Model):
    class Meta:
        db_table = "{self.name}"
{fields}
"""


@dataclasses.dataclass
class PSLDatasource:
    pass


@dataclasses.dataclass
class PSLGenerator:
    pass


@dataclasses.dataclass
class PSL:
    models: list[PSLModel]
    datasources: list[PSLDatasource]
    generator: Optional[PSLGenerator]
