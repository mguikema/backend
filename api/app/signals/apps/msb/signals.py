from rest_framework.exceptions import ValidationError
from signals.apps.signals.models import Signal
from signals.apps.msb.models import Melding
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from datetime import datetime
import json

@receiver(pre_save, sender=Melding, dispatch_uid="melding_pre_save")
def melding_pre_save(sender, instance, **kwargs):
    print("melding_pre_save")
    if instance.id is None and instance.msb_id:
        if not instance.msb_id:
            raise ValidationError()
        try:
            Melding.objects.get(msb_id=instance.msb_id)
        except Melding.DoesNotExist:
            print("DoesNotExist")
            if instance.msb_item:
                msbm = json.loads(instance.msb_item)
            if instance.msb_list_item:
                msbm = json.loads(instance.msb_list_item)
            else:
                raise ValidationError
            s = Signal()
            s.incident_date_start = datetime.strptime(msbm["datumMelding"], "%Y-%m-%dT%H:%M:%S")
            s.save()
            s.created_at = datetime.strptime(msbm["datumMelding"], "%Y-%m-%dT%H:%M:%S")
            s.save()
            instance.signal = s
        else:
            print("prevent signal/melding creation")
            raise ValidationError()
    elif instance.id is not None:
        current = instance
        previous = Melding.objects.get(id=instance.id)
        print(current.msb_list_item)
        print(previous.msb_list_item)
        if current.msb_item != previous.msb_item or current.msb_list_item != previous.msb_list_item:
            print("rebuild signal related")
            current.update_signal_relations = True
        else:
            print("signal data in sync with msb data")


@receiver(post_save, sender=Melding, dispatch_uid="melding_post_save")
def melding_post_save(sender, instance, created, **kwargs):
    print("melding_post_save")
    if instance.update_signal_relations:
        print("update_signal_relations")
        instance.update_signal()
        instance.update_signal_relations = False
    # if not created:
    #     current = instance
    #     previous = Melding.objects.get(id=instance.id)
    #     # print(current.msb_list_item)
    #     # print(previous.msb_list_item)
    #     if current.msb_item != previous.msb_item or current.msb_list_item != previous.msb_list_item:
    #         print("rebuild signal related")
    #     else:
    #         print("signal data in sync with msb data")
    # else:
    #     print("prevent signal/melding creation post save")

