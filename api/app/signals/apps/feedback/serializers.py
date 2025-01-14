# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from signals.apps.email_integrations.services import MailService
from signals.apps.feedback.models import Feedback, StandardAnswer
from signals.apps.feedback.utils import merge_texts, validate_answers
from signals.apps.signals import workflow
from signals.apps.signals.models import Signal


class StandardAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardAnswer
        fields = ('is_satisfied', 'text')


class FeedbackSerializer(serializers.ModelSerializer):
    signal_id = serializers.UUIDField(source='_signal.uuid', read_only=True)

    class Meta:
        model = Feedback
        fields = ('is_satisfied', 'allows_contact', 'text',
                  'text_list', 'text_extra', 'signal_id')
        # The 'required': True for is_satisfied field is only validated for JSON
        # updloads, a form upload defaults to False if is_satisfied is left out.
        # See the Django Rest Framework docs:
        # https://www.django-rest-framework.org/api-guide/fields/#booleanfield
        extra_kwargs = {
            'is_satisfied': {'write_only': True, 'required': True},
            'allows_contact': {'write_only': True},
            'text': {'write_only': True, 'required': False},
            'text_list': {'write_only': True, 'required': False},
            'text_extra': {'write_only': True},
        }

    def validate(self, attrs):
        """
        Validate if either text of text_list is filled in
        """
        if attrs.get('text') or attrs.get('text_list'):
            return attrs

        raise ValidationError({
            "non_field_errors": [
                "Either text or text_list must be filled in"
            ]
        })

    def update(self, instance, validated_data):
        # TODO: consider whether using a StandardAnswer while overriding the
        # is_satisfied field should be considered an error condition and return
        # an HTTP 400.
        validated_data['submitted_at'] = timezone.now()

        # Check whether the relevant Signal instance should possibly be
        # reopened (i.e. transition to VERZOEK_TOT_HEROPENEN state).
        is_satisfied = validated_data['is_satisfied']

        # @TODO: When text field is depricated the following can be removed
        validated_data = merge_texts(validated_data)
        instance.text = None
        instance.text_list = validated_data['text_list']

        reopen = False
        if not is_satisfied:
            reopen = validate_answers(validated_data)

        # Reopen the Signal (melding) if need be.
        if reopen:
            signal = instance._signal

            # Only allow a request to reopen when in state workflow.AFGEHANDELD
            if signal.status.state == workflow.AFGEHANDELD:
                payload = {
                    'text': 'De melder is niet tevreden blijkt uit feedback. Zo nodig heropenen.',
                    'state': workflow.VERZOEK_TOT_HEROPENEN,
                }
                Signal.actions.update_status(payload, signal)

        instance = super().update(instance, validated_data)
        # trigger the mail to be after the instance update to have the new data
        if not is_satisfied and instance._signal.allows_contact:
            MailService.system_mail(signal=instance._signal,
                                    action_name='feedback_received',
                                    feedback=instance)
        return instance
