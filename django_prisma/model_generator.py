import dataclasses
from lark import Lark, Transformer
from typing import Optional

grammar = """
?start: (generator | datasource | model)+

generator: "generator" IDENTIFIER "{" generator_body "}"
generator_body: (IDENTIFIER "=" STRING | IDENTIFIER "=" "[" string_list "]")*

datasource: "datasource" IDENTIFIER "{" datasource_body "}"
datasource_body: (IDENTIFIER "=" STRING | IDENTIFIER "=" "env" "(" STRING ")")*

model: "model" IDENTIFIER "{" (field | opt_field | arr_field | block_attributes)* "}"

field: IDENTIFIER TYPE attributes*
opt_field: IDENTIFIER TYPE "?" attributes*
arr_field: IDENTIFIER TYPE "[" "]" attributes*

block_attributes: unique_constraint
unique_constraint: "@@unique" "(" "[" identifier_list "]" ")"

attributes: "@" IDENTIFIER
          | "@" IDENTIFIER "(" STRING ")"
          | "@" IDENTIFIER "(" IDENTIFIER ")"
          | "@" IDENTIFIER "(" IDENTIFIER "(" ")" ")"
          | "@" "default" "(" default_body ")"
          | "@" "relation" "(" relation_body ")"
          | "@" "relation" "(" relation_body ")"

relation_body: IDENTIFIER ":" "[" identifier_list "]" "," IDENTIFIER ":" "[" identifier_list "]"
default_body: IDENTIFIER "(" ")"

string_list: STRING ("," STRING)*
identifier_list: IDENTIFIER ("," IDENTIFIER)*

TYPE: IDENTIFIER
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
STRING: /"[^"]*"/
ARRAY: "[" "]"
OPTIONAL: "?"

%import common.WS
%ignore WS
"""

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
class AttributeOptional(Attribute):
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


@dataclasses.dataclass
class CompoundUniqueConstraint:
    fields: list[str]

@dataclasses.dataclass
class PSLModel:
    name: str
    columns: list[PSLColumn]
    compound_unique_constraints: list[CompoundUniqueConstraint]

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

class PSLTransformer(Transformer):
    identifier_list = list
    string_list = list

    def model(self, items):
        name, *cols_and_constraints = items
        cols = []
        constraints = []
        for item in cols_and_constraints:
            match item:
                case CompoundUniqueConstraint(_):
                    constraints.append(item)
                case _:
                    cols.append(item)
        return PSLModel(name, cols, constraints)

    def unique_constraint(self, items):
        return CompoundUniqueConstraint(list(items))

    def attributes(self, items):
        ret = []
        for item in items:
            match item:
                case "id":
                    ret.append(AttributePK())
                case "unique":
                    ret.append(AttributeUnique())
                case AttributeDefaultAutoinc():
                    ret.append(item)
                case _:
                    print("other attr modifiers", item)
                    ret.append(item)
        return ret

    def default_body(self, items):
        item = items[0]
        match item:
            case "autoincrement":
                return AttributeDefaultAutoinc()
            case _:
                assert False, f"Did not deal with {item}"

    def relation_body(self, items):
        pairs = {items[i]: items[i+1] for i in range(0, len(items), 2)}
        local = pairs['fields']
        remote = pairs['references']
        return AttributeRelation(local_field_name=local, remote_field_name=remote)

    def opt_field(self, items):
        name, type_, *modifiers = items
        return PSLColumn(name, type_, props=modifiers, is_array=False, is_opt=True)

    def arr_field(self, items):
        name, type_, *modifiers = items
        return PSLColumn(name, type_, props=modifiers, is_array=True, is_opt=False)

    def field(self, items):
        name, type_, *modifiers = items
        flattened_modifiers = [item for sublist in modifiers for item in sublist]
        return PSLColumn(name, type_, props=flattened_modifiers, is_array=False, is_opt=False)


    def IDENTIFIER(self, items):
        return str(items)

    def TYPE(self, items):
        match items:
            case "Int":
                return Int()
            case "String":
                return String()
            case _:
                return UserDefinedType(str(items))

_parser = Lark(grammar, parser='lalr', transformer=PSLTransformer())

def parse_prisma_schema(text: str) -> PSL:
    result = _parser.parse(text)
    datasources = []
    models = []
    generator = None
    for child in result.children:
        match child:
            case PSLModel(_):
                models.append(child)
            case PSLDatasource(_):
                datasources.append(child)
            case PSLGenerator(_):
                assert generator is None
                generator = child
    return PSL(models, datasources, generator)
