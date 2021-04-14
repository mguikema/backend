# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 Gemeente Amsterdam
from datapunt_api.rest import HALSerializer
from rest_framework import serializers

from signals.apps.api.fields import PrivateSignalLinksField, PrivateSignalWithContextLinksField
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal


class ReporterContextSignalSerializer(HALSerializer):
    serializer_url_field = PrivateSignalLinksField

    newest_feedback = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Signal
        fields = (
            '_links',
            'id',
            'created_at',
            'status',
            'newest_feedback'
        )

    def get_status(self, obj):
        return {
            'state': obj.status.state,
            'state_display': obj.status.get_state_display(),
        }

    def get_newest_feedback(self, obj):
        if obj.newest_feedback:
            return {
                'is_satisfied': obj.newest_feedback[0].is_satisfied,
                'submitted_at': obj.newest_feedback[0].submitted_at,
            }
        return None


class SignalContextReporterSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    latest_feedback = serializers.SerializerMethodField()
    can_view_signal = serializers.SerializerMethodField()

    class Meta:
        model = Signal
        fields = (
            'id',
            'created_at',
            'category',
            'status',
            'latest_feedback',
            'can_view_signal',
        )

    def get_category(self, obj):
        departments = ', '.join(
            obj.category_assignment.category.departments.filter(
                categorydepartment__is_responsible=True
            ).values_list('code', flat=True)
        )
        return {
            'sub': obj.category_assignment.category.name,
            'sub_slug': obj.category_assignment.category.slug,
            'departments': departments,
            'main': obj.category_assignment.category.parent.name,
            'main_slug': obj.category_assignment.category.parent.slug,
        }

    def get_status(self, obj):
        return {'state': obj.status.state, 'state_display': obj.status.get_state_display(), }

    def get_latest_feedback(self, obj):
        if obj.feedback.exists():
            latest_feedback = obj.feedback.first()
            return {'is_satisfied': latest_feedback.is_satisfied, 'submitted_at': latest_feedback.submitted_at, }

    def get_can_view_signal(self, obj):
        return Signal.objects.filter(pk=obj.pk).filter_for_user(self.context['request'].user).exists()


class SignalContextSerializer(HALSerializer):
    serializer_url_field = PrivateSignalWithContextLinksField

    geography = serializers.SerializerMethodField(method_name='get_geography')
    reporter = serializers.SerializerMethodField(method_name='get_reporter')

    class Meta:
        model = Signal
        fields = (
            '_links',
            'geography',
            'reporter',
        )

    def get_geography(self, obj):
        return {
            'signal_count': 0,
        }

    def get_reporter(self, obj):
        if not obj.reporter.email:
            signals_for_reporter_count = 1
            open_signals_for_reporter_count = 1 if obj.status.state not in [workflow.GEANNULEERD, workflow.AFGEHANDELD, workflow.GESPLITST] else 0 # noqa
            satisfied_count = not_satisfied_count = 0
        else:
            reporter_email = obj.reporter.email

            signals_for_reporter_count = Signal.objects.filter_reporter(email=reporter_email).count()
            open_signals_for_reporter_count = Signal.objects.filter_reporter(email=reporter_email).exclude(
                status__state__in=[workflow.GEANNULEERD, workflow.AFGEHANDELD, workflow.GESPLITST]
            ).count()
            satisfied_count = Signal.objects.reporter_feedback_satisfied_count(email=reporter_email)
            not_satisfied_count = Signal.objects.reporter_feedback_not_satisfied_count(email=reporter_email)

        return {
            'signal_count': signals_for_reporter_count,
            'open_count': open_signals_for_reporter_count,
            'positive_count': satisfied_count,
            'negative_count': not_satisfied_count,
        }
