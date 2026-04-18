"""
Schema step 2: now that every Person has a party_id (populated by 0003),
  - make Person.party non-nullable
  - remove Person.is_active, Person.created_by, Person.categories (M2M)
  - drop PersonCategoryAssignment, PersonCategory, PersonAddress,
    PersonNote, PersonAttachment, OrganizationPersonRelation

After this migration the people app contains only the Person model.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("people", "0003_migrate_to_party"),
    ]

    operations = [
        # ── 1. Make party FK non-nullable ──────────────────────────────────────
        migrations.AlterField(
            model_name="person",
            name="party",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="person",
                to="party.party",
            ),
        ),

        # ── 2. Remove Person fields that moved to Party ────────────────────────
        # Remove M2M accessor first (before deleting the through model)
        migrations.RemoveField(
            model_name="person",
            name="categories",
        ),
        migrations.RemoveField(
            model_name="person",
            name="created_by",
        ),
        migrations.RemoveField(
            model_name="person",
            name="is_active",
        ),

        # ── 3. Drop old sub-resource models ────────────────────────────────────
        # PersonCategoryAssignment has FKs to Person and PersonCategory;
        # drop it before dropping either referenced model.
        migrations.DeleteModel(name="PersonCategoryAssignment"),
        migrations.DeleteModel(name="PersonCategory"),
        migrations.DeleteModel(name="PersonAddress"),
        migrations.DeleteModel(name="PersonNote"),
        migrations.DeleteModel(name="PersonAttachment"),
        migrations.DeleteModel(name="OrganizationPersonRelation"),
    ]
