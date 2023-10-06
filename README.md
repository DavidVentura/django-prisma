This repo is a proof of concept for a database back-end for Prisma (Accelerate) with Django.
It works for basic stuff and can even open the Admin panel!

## Example

You can specify per-queryset cache-strategies (or no caching):

```python
cs = CacheStrategy(ttl=60, swr=60)
users_fast = User.objects.with_cache(cs).all()
users_slow = User.objects.all()
```

## Problems

A lot of features are missing, anything behind very basic querying won't work.

The migration roundtrip breaks without manual intervention:
  - `manage.py migrate`
  - `prisma db pull`
  - `manage.py runserver`

This is because when running `prisma db pull`, the generated names for foreign keys don't match the database:

As an example, the `auth_permission` table has a `content_type` foreign key.
```
prismatest=# select * from "auth_permission";
 id |          name           | content_type_id |      codename      
----+-------------------------+-----------------+--------------------
  1 | Can add user            |               1 | add_user
```

But `prisma db pull` calls the field `django_content_type`, which later breaks django.

Renaming the FK fields to remove the (Django) app-name from them makes this work again.

## How to use it

(Don't)

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
