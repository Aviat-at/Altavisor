"""
Schema step 1: add a nullable party FK to Person.

Old sub-resource models (PersonCategory, PersonAddress, etc.) are NOT yet
removed here — they must still exist in the migration state so that the
data migration (0003) can read from them.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("party", "0001_initial"),
        ("people", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="party",
            field=models.OneToOneField(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="person",
                to="party.party",
            ),
        ),
    ]
