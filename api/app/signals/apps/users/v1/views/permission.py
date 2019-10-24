from datapunt_api.rest import DatapuntViewSet
from django.contrib.auth.models import Permission
from rest_framework.permissions import DjangoModelPermissions

from signals.apps.api.generics.permissions import SIAPermissions
from signals.apps.users.v1.serializers import PermissionSerializer
from signals.auth.backend import JWTAuthBackend


class PermissionViewSet(DatapuntViewSet):
    queryset = Permission.objects.prefetch_related(
        'content_type',
    ).all()

    authentication_classes = (JWTAuthBackend,)
    permission_classes = (SIAPermissions & DjangoModelPermissions,)

    serializer_detail_class = PermissionSerializer
    serializer_class = PermissionSerializer
