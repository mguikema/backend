from rest_framework import serializers
from django.utils.text import slugify
from signals.apps.signals.models.category import Category
from signals.apps.api.serializers.nested import _NestedCategoryModelSerializer

class OnderwerpSerializer(serializers.Serializer):
    id = serializers.CharField()
    omschrijving = serializers.CharField()

class AfdelingSerializer(serializers.Serializer):
    id = serializers.CharField()
    omschrijving = serializers.CharField()

class AdresSerializer(serializers.Serializer):
    straatNummer = serializers.CharField()
    straatNaam = serializers.CharField()
    huisnummer = serializers.CharField()

class LocatieSerializer(serializers.Serializer):
    adres = AdresSerializer()
    x = serializers.IntegerField()
    y = serializers.IntegerField()

class MeldingListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    spoed = serializers.BooleanField()
    datumMelding = serializers.DateTimeField()
    datumInbehandeling = serializers.DateTimeField(
        allow_null=True,
        required=False,
    )
    werkdagenSindsRegistratie = serializers.FloatField()
    datumRappel = serializers.DateTimeField(
        allow_null=True,
        required=False,
    )
    herkomstCode = serializers.CharField()
    status = serializers.CharField()
    onderwerp = OnderwerpSerializer()
    afdeling = AfdelingSerializer()
    locatie = LocatieSerializer()

def map_msb_list_item_on_signal(msb_item_list):
    msb_item_list_serializer = MeldingListSerializer(data=msb_item_list, many=True)
    msb_data = []
    if msb_item_list_serializer.is_valid():
        msb_data = msb_item_list_serializer.data
    def get_sub_category(sub_slug):
        sub_category = Category.objects.filter(slug=sub_slug, parent__isnull=False).first()
        if not sub_category:
            sub_category = Category.objects.filter(slug="overig", parent__isnull=False).first()
        return sub_category
    def get_location():
        pass

    signal_data = [{
        "assigned_user_email": None,
        "category": {
            # "sub_category": get_sub_category(slugify(m["onderwerp"]["omschrijving"])).get_absolute_url(),
            "category_url": get_sub_category(slugify(m["onderwerp"]["omschrijving"])).get_absolute_url(),
            "created_by": "todo@example.com",
            "departments": "",
            "deadline": None,
            "deadline_factor_3": None,
            "main": get_sub_category(slugify(m["onderwerp"]["omschrijving"])).parent.name,
            "main_slug": get_sub_category(slugify(m["onderwerp"]["omschrijving"])).parent.slug,
            "sub": m["onderwerp"]["omschrijving"],
            "sub_slug": slugify(m["onderwerp"]["omschrijving"]),
            "text": None,
        },
        "created_at": m["datumMelding"],
        "extra_properties": None,
        "has_attachments": False,
        "has_children": False,
        "has_parent": False,
        "has_parent": False,
        "msb_id": m["id"],
        "id_display": "SIG_0",
        "incident_date_end": None,
        "incident_date_start": m["datumMelding"],
        "location": {
            "address": {
                "huisnummer": m.get("locatie", {}).get("adres", {}).get("huisnummer"),
                "openbare_ruimte": m["locatie"].get("adres", {}).get("straatNaam"),
                "woonplaats": "Rotterdam",
            },
            "geometrie": {"type":"Point","coordinates":[4.4777998357861435,51.92249777094102]},
        },
        "text": "originele melding tekst",
        "priority": {"priority":"normal"},
        "reporter": {"sharing_allowed":True},
    } for m in msb_data]
    return signal_data
