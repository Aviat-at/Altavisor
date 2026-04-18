"""
Data migration: populate party.Party rows and copy all Person sub-resources
to the shared party tables.

Steps:
  a) PersonCategory     → party.PartyCategory
  b) Person             → party.Party (one per person)
  c) PersonAddress      → party.PartyAddress
  d) PersonNote         → party.PartyNote
  e) PersonAttachment   → party.PartyAttachment
  f) PersonCategoryAssignment → party.PartyCategoryAssignment
  g) OrganizationPersonRelation → party.PartyRelationship
     to_party is set to None because no Company Party exists yet.
     It will be resolved when the companies app ships.

Reverse migration is a no-op: the party tables are dropped by their own
app's migrations if needed; reverse here would leave stale party rows which
is acceptable since party is the authoritative source going forward.
"""
import logging

from django.db import migrations

logger = logging.getLogger(__name__)


def migrate_forward(apps, schema_editor):
    # ── Historical model accessors ─────────────────────────────────────────────
    Person = apps.get_model("people", "Person")
    PersonCategory = apps.get_model("people", "PersonCategory")
    PersonCategoryAssignment = apps.get_model("people", "PersonCategoryAssignment")
    PersonAddress = apps.get_model("people", "PersonAddress")
    PersonNote = apps.get_model("people", "PersonNote")
    PersonAttachment = apps.get_model("people", "PersonAttachment")
    OrganizationPersonRelation = apps.get_model("people", "OrganizationPersonRelation")

    Party = apps.get_model("party", "Party")
    PartyCategory = apps.get_model("party", "PartyCategory")
    PartyCategoryAssignment = apps.get_model("party", "PartyCategoryAssignment")
    PartyAddress = apps.get_model("party", "PartyAddress")
    PartyNote = apps.get_model("party", "PartyNote")
    PartyAttachment = apps.get_model("party", "PartyAttachment")
    PartyRelationship = apps.get_model("party", "PartyRelationship")

    # ── a) Migrate PersonCategory → PartyCategory ──────────────────────────────
    # Build a map from old id → new id for use in assignment migration below.
    category_id_map: dict[int, int] = {}

    for pc in PersonCategory.objects.all():
        party_cat = PartyCategory.objects.create(
            name=pc.name,
            slug=pc.slug,
            description=pc.description,
            is_system=pc.is_system,
            is_active=pc.is_active,
        )
        # Preserve created_at / updated_at (auto_now* fields require .update())
        PartyCategory.objects.filter(pk=party_cat.pk).update(
            created_at=pc.created_at,
            updated_at=pc.updated_at,
        )
        category_id_map[pc.pk] = party_cat.pk

    # ── b-g) One pass per Person ───────────────────────────────────────────────
    for person in Person.objects.all().order_by("id"):
        # b) Create the Party root record
        party = Party.objects.create(
            party_type="person",
            is_active=person.is_active,
            created_by_id=person.created_by_id,
        )
        # Preserve original created_at (auto_now_add prevents direct assignment)
        Party.objects.filter(pk=party.pk).update(created_at=person.created_at)

        # Link person → party
        Person.objects.filter(pk=person.pk).update(party_id=party.pk)
        person.party_id = party.pk  # keep in-memory reference current

        # c) Addresses
        for addr in PersonAddress.objects.filter(person_id=person.pk):
            pa = PartyAddress.objects.create(
                party_id=party.pk,
                label=addr.label,
                line1=addr.line1,
                line2=addr.line2,
                city=addr.city,
                state_province=addr.state_province,
                postal_code=addr.postal_code,
                country=addr.country,
                is_default=addr.is_default,
                is_active=addr.is_active,
            )
            PartyAddress.objects.filter(pk=pa.pk).update(
                created_at=addr.created_at,
                updated_at=addr.updated_at,
            )

        # d) Notes
        for note in PersonNote.objects.filter(person_id=person.pk):
            pn = PartyNote.objects.create(
                party_id=party.pk,
                body=note.body,
                author_id=note.author_id,
            )
            PartyNote.objects.filter(pk=pn.pk).update(created_at=note.created_at)

        # e) Attachments
        for att in PersonAttachment.objects.filter(person_id=person.pk):
            pa2 = PartyAttachment.objects.create(
                party_id=party.pk,
                label=att.label,
                file=att.file,
                uploaded_by_id=att.uploaded_by_id,
            )
            PartyAttachment.objects.filter(pk=pa2.pk).update(created_at=att.created_at)

        # f) Category assignments
        for ca in PersonCategoryAssignment.objects.filter(person_id=person.pk):
            new_cat_id = category_id_map.get(ca.category_id)
            if new_cat_id is None:
                logger.warning(
                    "PersonCategoryAssignment id=%s references unknown category id=%s "
                    "— skipping.",
                    ca.pk, ca.category_id,
                )
                continue
            pca = PartyCategoryAssignment.objects.create(
                party_id=party.pk,
                category_id=new_cat_id,
                assigned_by_id=ca.assigned_by_id,
                is_active=ca.is_active,
            )
            PartyCategoryAssignment.objects.filter(pk=pca.pk).update(
                created_at=ca.created_at,
                updated_at=ca.updated_at,
            )

        # g) Org relations — to_party is NULL until companies app ships
        for rel in OrganizationPersonRelation.objects.filter(person_id=person.pk):
            logger.warning(
                "OrganizationPersonRelation id=%s (person=%s, %s#%s, role=%s) cannot "
                "be fully migrated: no Company Party exists yet. "
                "to_party_id will be NULL. Resolve when the companies app ships.",
                rel.pk, person.pk, rel.organization_type, rel.organization_id, rel.role,
            )
            pr = PartyRelationship.objects.create(
                from_party_id=party.pk,
                to_party=None,
                role=rel.role,
                is_primary=rel.is_primary,
                is_active=rel.is_active,
                started_on=rel.started_on,
                ended_on=rel.ended_on,
            )
            PartyRelationship.objects.filter(pk=pr.pk).update(
                created_at=rel.created_at,
                updated_at=rel.updated_at,
            )


def migrate_backward(apps, schema_editor):
    # Reverse is a deliberate no-op: we leave party rows in place.
    # If a full rollback is needed, drop and recreate the party app tables.
    pass


class Migration(migrations.Migration):

    dependencies = [
        # people/0002 adds the nullable party FK to Person
        ("people", "0002_person_add_party_link"),
        # party/0002 makes to_party nullable on PartyRelationship
        ("party", "0002_partyrelationship_to_party_nullable"),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
    ]
