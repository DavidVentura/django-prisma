from django_prisma.psl_types import *
from django_prisma.psl_parser import parse_prisma_schema



def test_parse_schema():
    data = """
    generator client {
      provider        = "prisma-client-js"
      previewFeatures = ["clientExtensions", "other_value"]
    }

    datasource db {
      provider  = "postgresql"
      url       = env("DATABASE_URL")
      directUrl = env("DIRECT_URL")
    }
    model User {
      id    Int     @id @default(autoincrement())
      email String  @unique
      name  String?
      pets  Pet[]
    }

    model Pet {
      id      Int    @id @default(autoincrement())
      name    String
      ownerId Int
      owner   User   @relation(fields: [ownerId], references: [id])
    }
    """
    res = parse_prisma_schema(data)
    assert res == PSL(
        models=[
            PSLModel(
                name="User",
                columns=[
                    PSLColumn(
                        name="id",
                        type_=Int(),
                        props=[AttributePK(), AttributeDefaultAutoinc()],
                        is_array=False,
                        is_opt=False,
                    ),
                    PSLColumn(name="email", type_=String(), props=[AttributeUnique()], is_array=False, is_opt=False),
                    PSLColumn(name="name", type_=String(), props=[], is_array=False, is_opt=True),
                    PSLColumn(name="pets", type_=UserDefinedType(name="Pet"), props=[], is_array=True, is_opt=False),
                ],
                compound_unique_constraints=[],
            ),
            PSLModel(
                name="Pet",
                columns=[
                    PSLColumn(
                        name="id",
                        type_=Int(),
                        props=[AttributePK(), AttributeDefaultAutoinc()],
                        is_array=False,
                        is_opt=False,
                    ),
                    PSLColumn(name="name", type_=String(), props=[], is_array=False, is_opt=False),
                    PSLColumn(name="ownerId", type_=Int(), props=[], is_array=False, is_opt=False),
                    PSLColumn(
                        name="owner",
                        type_=UserDefinedType(name="User"),
                        props=[AttributeRelation(local_field_name=["ownerId"], remote_field_name=["id"])],
                        is_array=False,
                        is_opt=False,
                    ),
                ],
                compound_unique_constraints=[],
            ),
        ],
        datasources=[],
        generator=None,
    )


    print(res.models[0].to_django_model())

def test_render_model():
    data = """
    model User {
      id    Int     @id @default(autoincrement())
      email String  @unique
      name  String?
      pets  Pet[]
    }

    model Pet {
      id      Int    @id @default(autoincrement())
      name    String
      ownerId Int
      owner   User   @relation(fields: [ownerId], references: [id])
    }
    """
    res = parse_prisma_schema(data)

    expected_user = """
class User(models.Model):
    class Meta:
        db_table = "User"
    id = models.AutoField(primary_key=True)
    email = models.CharField(unique=True)
    name = models.CharField(null=True)
"""
    expected_pet = """
class Pet(models.Model):
    class Meta:
        db_table = "Pet"
    id = models.AutoField(primary_key=True)
    name = models.CharField()
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE, db_column="ownerId")
"""
    assert res.models[0].to_django_model() == expected_user
    assert res.models[1].to_django_model() == expected_pet
