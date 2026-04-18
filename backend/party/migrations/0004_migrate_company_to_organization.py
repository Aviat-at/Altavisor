# Generated migration to update party_type from 'company' to 'organization'

from django.db import migrations


def migrate_company_to_organization(apps, schema_editor):
    """Update all Party records with party_type='company' to 'organization'."""
    Party = apps.get_model('party', 'Party')
    Party.objects.filter(party_type='company').update(party_type='organization')


def reverse_migration(apps, schema_editor):
    """Reverse the migration (update 'organization' back to 'company')."""
    Party = apps.get_model('party', 'Party')
    Party.objects.filter(party_type='organization').update(party_type='company')


class Migration(migrations.Migration):

    dependencies = [
        ('party', '0003_rename_company_to_organization'),
    ]

    operations = [
        migrations.RunPython(migrate_company_to_organization, reverse_migration),
    ]
