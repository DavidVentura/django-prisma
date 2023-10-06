This repo is a proof of concept for a database back-end for Prisma (Accelerate) with Django.

## Example

Configure your back-end to use this backend by setting your token and schema path.

```python
DATABASES = {
    'default': {
        'ENGINE': 'django_prisma',
        'TOKEN': 'fill me in',
        'SCHEMA_PATH': 'fill me in',
    }
}

```

Then, generate the Django models from the `schema.prisma`

```prisma
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
```

```bash
python django_prisma/psl_parser.py ../prisma/schema.prisma > users/models.py
```

will generate `users/models.py`:

```python
class User(models.Model):
    class Meta:
        db_table = "User"
    id = models.AutoField(primary_key=True)
    email = models.CharField(unique=True)
    name = models.CharField(null=True)


class Pet(models.Model):
    class Meta:
        db_table = "Pet"
    id = models.AutoField(primary_key=True)
    name = models.CharField()
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE, db_column="ownerId")
```

That's it, you can use basic features (select, insert) normally:

```python
User.objects.create(name="a name", email="definitely an email address")

# Fetch Single object
user = User.objects.get(name="i just created this")

# Basic lookup
for user in User.objects.all():
    print(user.name)

# Lazy lookup
for pet in Pet.objects.all():
    print(pet.id, pet.name)
    print("owner (with lazy lookup)", pet.owner)

# with "IN" lookup for id
for p in Pet.objects.all().prefetch_related("owner"):
    print("pet", p, p.id, p.name)
    print("owner (without a lazy query)", p.owner)

# with JOIN
for p in Pet.objects.all().select_related("owner"):
    print("pet", p, p.id, p.name)
    print("owner (without a lazy query)", p.owner)
```
