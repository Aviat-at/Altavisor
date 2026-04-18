"""
Make PartyRelationship.to_party nullable so that legacy OrganizationPersonRelation
rows can be migrated without a real target Party. to_party will be populated once
the companies app ships and Company records are linked to Party rows.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("party", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="partyrelationship",
            name="to_party",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="relationships_as_org",
                to="party.party",
            ),
        ),
    ]
