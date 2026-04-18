from django.contrib import admin

from .models import (
    Party,
    PartyAddress,
    PartyAttachment,
    PartyCategory,
    PartyCategoryAssignment,
    PartyNote,
    PartyRelationship,
)

admin.site.register(Party)
admin.site.register(PartyCategory)
admin.site.register(PartyCategoryAssignment)
admin.site.register(PartyAddress)
admin.site.register(PartyNote)
admin.site.register(PartyAttachment)
admin.site.register(PartyRelationship)
