This repo is a proof of concept for a database back-end for Prisma (Accelerate) with Django.

This does not manage the database schema yet, so you must ensure your models match what you've defined in `schema.prisma`.


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

Then, ensure the Django model matches the `schema.prisma`

```prisma
model User {
  id    Int     @id @default(autoincrement())
  email String  @unique
  name  String?
}
```

and `users/models.py`

```python
class User(models.Model):
    class Meta:
        db_table = 'User'
    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200, null=True)

    objects = models.Manager()
    with_cache = CacheableManager(swr=60, ttl=60)


class Pet(models.Model):
    class Meta:
        db_table = 'Pet'
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE, db_column='ownerId')
```

That's it, you can use basic features (select, insert) normally:

```python
User.objects.create(name="askdjask", email="askdjask")

# Single object
user = User.objects.get(name='i just created this')

# Basic lookup
for user in User.objects.all():
    print(user.name)

# Lazy lookup
for pet in Pet.objects.all():
    print(pet.id, pet.name)
    print("with lazy lookup", pet.owner)

# with "IN" lookup for id
for p in Pet.objects.all().prefetch_related("owner"):
    print('pet', p, p.id, p.name)
    print('owner (no query?)', p.owner)

# with JOIN
for p in Pet.objects.all().select_related("owner"):
    print('pet', p, p.id, p.name)
    print('owner (no query?)', p.owner)

# Using Accelerate's cache strategy (kinda)
User.with_cache.all()
```
