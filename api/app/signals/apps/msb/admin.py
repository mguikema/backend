# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2022 Gemeente Amsterdam
from django.contrib import admin
from django.db import transaction

from signals.apps.msb.models import Melding
from signals.apps.signals.models import Status


class MeldingAdmin(admin.ModelAdmin):
    pass

admin.site.register(Melding, MeldingAdmin)