# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from datapunt_api.rest import DatapuntViewSetWritable
from django.contrib.auth.models import Group
from django.db.models.functions import Lower
from rest_framework.permissions import DjangoModelPermissions

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.users.v1.serializers import RoleSerializer
from signals.auth.backend import AuthBackend


class RoleViewSet(DatapuntViewSetWritable):
    queryset = Group.objects.prefetch_related(
        'permissions',
        'permissions__content_type',
    ).order_by(Lower('name'))

    authentication_classes = (AuthBackend,)
    permission_classes = (SIAPermissions & DjangoModelPermissions, )

    serializer_detail_class = RoleSerializer
    serializer_class = RoleSerializer
