# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.apps import AppConfig


class MSBConfig(AppConfig):
    name = 'signals.apps.msb'
    verbose_name = 'MSB'

    def ready(self):
        import signals.apps.msb.signals  # noqa

