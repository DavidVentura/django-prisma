This repo is a proof of concept for a database back-end for Prisma (Accelerate) with Django.

This does not manage the database schema yet, so you must ensure your models match what you've defined in `schema.prisma`.


## Example

Configure your back-end to use this back end and set your token

```python
DATABASES = {
    'default': {
        'ENGINE': 'django_prisma',
        'TOKEN': 'fill me in',
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
```

That's it, you can use basic features (select, insert) normally:

```python
User.objects.create(name="i just created this, again",
                    email="some@email-value-2")

user = User.objects.get(name='i just created this')
print(user, user.id, user.name, user.email)

for user in User.objects.all():
    print(user, user.id, user.name, user.email)
```
