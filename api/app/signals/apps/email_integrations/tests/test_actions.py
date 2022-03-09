# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2021 - 2022 Gemeente Amsterdam
from datetime import timedelta
from unittest import mock
from urllib.parse import quote

from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from factory.fuzzy import FuzzyText
from freezegun import freeze_time

from signals.apps.email_integrations.actions import (
    SignalCreatedAction,
    SignalHandledAction,
    SignalOptionalAction,
    SignalReactionRequestAction,
    SignalReactionRequestReceivedAction,
    SignalReopenedAction,
    SignalScheduledAction
)
from signals.apps.email_integrations.models import EmailTemplate
from signals.apps.signals import workflow
from signals.apps.signals.factories import SignalFactory, StatusFactory
from signals.apps.signals.models import Note


class ActionTestMixin:
    send_email = False

    def setUp(self):
        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_CREATED,
                                     title='Uw melding {{ signal_id }}'
                                           f' {EmailTemplate.SIGNAL_CREATED}',
                                     body='{{ text }} {{ created_at }} {{ handling_message }} {{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD,
                                     title='Uw melding {{ signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_AFGEHANDELD}',
                                     body='{{ text }} {{ created_at }} {{ positive_feedback_url }} '
                                          '{{ negative_feedback_url }}{{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_INGEPLAND,
                                     title='Uw melding {{ signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_INGEPLAND}',
                                     body='{{ text }} {{ created_at }} {{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_HEROPEND,
                                     title='Uw melding {{ signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_HEROPEND}',
                                     body='{{ text }} {{ created_at }} {{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_OPTIONAL,
                                     title='Uw melding {{ signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_OPTIONAL}',
                                     body='{{ text }} {{ created_at }} {{ status_text }} {{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD,
                                     title='Uw melding {{ signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_GEVRAAGD}',
                                     body='{{ text }} {{ created_at }} {{ status_text }} {{ reaction_url }} '
                                          '{{ ORGANIZATION_NAME }}')

        EmailTemplate.objects.create(key=EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_ONTVANGEN,
                                     title='Uw melding {{ signal_id }}'
                                           f' {EmailTemplate.SIGNAL_STATUS_CHANGED_REACTIE_ONTVANGEN}',
                                     body='{{ text }} {{ created_at }} {{ reaction_request_answer }} '
                                          '{{ ORGANIZATION_NAME }}')

    def test_send_email(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=200) if self.state == workflow.REACTIE_GEVRAAGD else FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='test@example.com')
        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.id} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_send_email_dry_run(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=200) if self.state == workflow.REACTIE_GEVRAAGD else FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='test@example.com')
        self.assertTrue(self.action(signal, dry_run=True))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    def test_send_email_anonymous(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=200) if self.state == workflow.REACTIE_GEVRAAGD else FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='')
        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email=None)
        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    def test_send_email_for_parent_signals(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=200) if self.state == workflow.REACTIE_GEVRAAGD else FuzzyText(length=400)
        parent_signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                             status__send_email=self.send_email, reporter__email='test@example.com')
        SignalFactory.create(status__state=self.state, status__text=status_text, reporter__email='test@example.com',
                             parent=parent_signal)
        self.assertTrue(self.action(parent_signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_do_not_send_email_for_child_signals(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=200) if self.state == workflow.REACTIE_GEVRAAGD else FuzzyText(length=400)
        parent_signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                             status__send_email=self.send_email, reporter__email='test@example.com')
        child_signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                            status__send_email=self.send_email, reporter__email='test@example.com',
                                            parent=parent_signal)
        self.assertFalse(self.action(child_signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    def test_do_not_send_email_invalid_states(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=200) if self.state == workflow.REACTIE_GEVRAAGD else FuzzyText(length=400)
        states = list(map(lambda x: x[0] and x[0] == self.state, workflow.STATUS_CHOICES))
        for state in states:
            signal = SignalFactory.create(status__state=state, status__text=status_text,
                                          status__send_email=True, reporter__email='test@example.com')
            self.assertFalse(self.action(signal))
            self.assertEqual(Note.objects.count(), 0)
            self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    @mock.patch('signals.apps.email_integrations.actions.abstract.send_mail', autospec=True)
    def test_send_email_fails(self, mocked):
        mocked.return_value = False

        self.assertEqual(len(mail.outbox), 0)

        status_text = FuzzyText(length=200) if self.state == workflow.REACTIE_GEVRAAGD else FuzzyText(length=400)
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=True, reporter__email='test@example.com')
        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)

    def test_send_mail_fails_encoded_chars_in_text(self):
        """
        The action should not send an email if the text contains encoded characters. A note should be added so that
        it is clear why the email was not sent. This is also logged in Sentry.
        """
        self.assertEqual(len(mail.outbox), 0)

        unquoted_url = 'https://user:password@test-domain.com/?query=param&extra=param'
        quoted_url = unquoted_url
        # Let's encode the URL 10 times
        for _ in range(10):
            quoted_url = quote(quoted_url)

        signal_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut ' \
                      f'labore et dolore magna aliqua. {quoted_url} Ut enim ad minim veniam, quis nostrud ' \
                      'exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.'

        status_text = FuzzyText(length=200)

        signal = SignalFactory.create(text=signal_text, text_extra=signal_text, status__state=self.state,
                                      status__text=status_text, status__send_email=True,
                                      reporter__email='test@example.com')
        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)

        signal.refresh_from_db()
        self.assertEqual(signal.notes.count(), 1)
        self.assertEquals(signal.notes.first().text,
                          'E-mail is niet verzonden omdat er verdachte tekens in de meldtekst staan.')


class TestSignalCreatedAction(ActionTestMixin, TestCase):
    """
    Test the SignalCreatedAction. The action should only be triggerd when the following rules apply:

    - The status is GEMELD
    - The status GEMELD is set only once
    """
    state = workflow.GEMELD
    action = SignalCreatedAction()

    def test_signal_set_state_second_time(self):
        """
        Check that if the status GEMELD is set for a second time the action is not triggered
        """
        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com')

        status = StatusFactory.create(_signal=signal, state=workflow.BEHANDELING)
        signal.status = status
        signal.save()

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())

    def test_signal_set_state_multiple_times(self):
        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com')

        for x in range(5):
            with freeze_time(timezone.now() + timedelta(hours=x)):
                status = StatusFactory.create(_signal=signal, state=self.state)
                signal.status = status
                signal.save()

        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Note.objects.count(), 0)
        self.assertFalse(Note.objects.filter(text=self.action.note).exists())


class TestSignalHandledAction(ActionTestMixin, TestCase):
    """
    Test the SignalHandledAction. The action should only be triggerd when the following rules apply:

    - The status is AFGEHANDELD
    - The previous state is not VERZOEK_TOT_HEROPENEN
    """
    state = workflow.AFGEHANDELD
    action = SignalHandledAction()

    def test_signal_set_state_second_time(self):
        """
        If the Signal status is set to AFGEHANDELD a second time and the previous state is not VERZOEK_TOT_HEROPENEN
        the action should be triggered
        """
        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

        status = StatusFactory.create(_signal=signal, state=workflow.HEROPEND)
        signal.status = status
        signal.save()

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(Note.objects.count(), 2)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

    def test_signal_set_state_second_time_second_last_state_verzoek_tot_heropenen(self):
        """
        If the Signal status is set to AFGEHANDELD a second time and the previous state is VERZOEK_TOT_HEROPENEN the
        action should not be triggered
        """
        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

        status = StatusFactory.create(_signal=signal, state=workflow.VERZOEK_TOT_HEROPENEN)
        signal.status = status
        signal.save()

        status = StatusFactory.create(_signal=signal, state=self.state)
        signal.status = status
        signal.save()

        self.assertFalse(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())


class TestSignalScheduledAction(ActionTestMixin, TestCase):
    """
    Test the SignalScheduledAction. The action should only be triggerd when the following rules apply:

    - The status is INGEPLAND
    - send_email must be True
    """
    state = workflow.INGEPLAND
    send_email = True
    action = SignalScheduledAction()


class TestSignalReopenedAction(ActionTestMixin, TestCase):
    """
    Test the SignalReopenedAction. The action should only be triggerd when the following rules apply:

    - The status is HEROPEND
    """
    state = workflow.HEROPEND
    action = SignalReopenedAction()


class TestSignalReactionRequestAction(ActionTestMixin, TestCase):
    """
    Test the SignalReactionRequestAction. The action should only be triggerd when the following rules apply:

    - The status is REACTIE_GEVRAAGD
    """
    state = workflow.REACTIE_GEVRAAGD
    action = SignalReactionRequestAction()

    def test_send_email(self):
        """
        Also check that the FRONTEND_URL is present in the message body
        """
        super().test_send_email()

        message = mail.outbox[0]
        self.assertIn(settings.FRONTEND_URL, message.body)
        self.assertIn(settings.FRONTEND_URL, message.alternatives[0][0])


class TestSignalReactionRequestReceivedAction(ActionTestMixin, TestCase):
    """
    Test the SignalReactionRequestReceivedAction. The action should only be triggerd when the following rules apply:

    - The status is REACTIE_ONTVANGEN
    - The status text does not match NO_REACTION_RECEIVED_TEXT
    """
    state = workflow.REACTIE_ONTVANGEN
    send_email = True
    action = SignalReactionRequestReceivedAction()

    def test_send_email(self):
        self.assertEqual(len(mail.outbox), 0)

        status_text = 'Aanvullend antwoord naar aanleiding van reactie gevraagd is gegeven.'
        signal = SignalFactory.create(status__state=self.state, status__text=status_text,
                                      status__send_email=self.send_email, reporter__email='test@example.com')
        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Uw melding {signal.id} {self.action.key}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())

        message = mail.outbox[0]
        self.assertIn(status_text, message.body)
        self.assertIn(status_text, message.alternatives[0][0])


class TestSignalOptionalAction(TestCase):
    """
    Test the SignalOptionalAction. The action should only be triggerd when the following rules apply:

    - The status is GEMELD, AFWACHTING, BEHANDELING, ON_HOLD, VERZOEK_TOT_AFHANDELING or GEANNULEERD
    - send_email must be True
    """
    action = SignalOptionalAction()

    def test_statuses(self):
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        statuses = [
            workflow.GEMELD,
            workflow.AFWACHTING,
            workflow.BEHANDELING,
            workflow.ON_HOLD,
            workflow.VERZOEK_TOT_AFHANDELING,
            workflow.GEANNULEERD,
        ]

        for state in statuses:
            status = StatusFactory.create(_signal=signal, state=state, send_email=True)
            signal.status = status
            signal.save()

            self.assertTrue(self.action(signal, dry_run=False))

    def test_statuses_do_not_apply(self):
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        statuses = [
            workflow.GEMELD,
            workflow.AFWACHTING,
            workflow.BEHANDELING,
            workflow.ON_HOLD,
            workflow.VERZOEK_TOT_AFHANDELING,
            workflow.GEANNULEERD,
        ]

        for state in statuses:
            status = StatusFactory.create(_signal=signal, state=state, send_email=False)
            signal.status = status
            signal.save()

            self.assertFalse(self.action(signal, dry_run=False))

    def test_statuses_not_allowed(self):
        signal = SignalFactory.create(status__state=workflow.GEMELD, reporter__email='test@example.com')

        statuses = [
            workflow.LEEG,
            workflow.AFGEHANDELD,
            workflow.GESPLITST,
            workflow.HEROPEND,
            workflow.INGEPLAND,
            workflow.VERZOEK_TOT_HEROPENEN,
            workflow.TE_VERZENDEN,
            workflow.VERZONDEN,
            workflow.VERZENDEN_MISLUKT,
            workflow.AFGEHANDELD_EXTERN,
        ]

        for state in statuses:
            status = StatusFactory.create(_signal=signal, state=state, send_email=True)
            signal.status = status
            signal.save()

            self.assertFalse(self.action(signal, dry_run=False))


class TestSignalCreatedActionNoTemplate(TestCase):
    """
    Test the SignalOptionalAction. No EmailTemplate(s) are present in the database, therefor the fallback template
    should be used. The action should only be triggerd when the following rules apply:

    - The status is GEMELD
    - The status GEMELD is set only once
    """
    state = workflow.GEMELD
    action = SignalCreatedAction()

    def test_send_email(self):
        self.assertEqual(EmailTemplate.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        signal = SignalFactory.create(status__state=self.state, reporter__email='test@example.com')
        self.assertTrue(self.action(signal, dry_run=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Bedankt voor uw melding {signal.id}')
        self.assertEqual(mail.outbox[0].to, [signal.reporter.email, ])
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(Note.objects.count(), 1)
        self.assertTrue(Note.objects.filter(text=self.action.note).exists())