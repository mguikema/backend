# SPDX-License-Identifier: MPL-2.0
# Copyright (C) 2019 - 2021 Gemeente Amsterdam
import logging

from django.contrib.gis.db import models
from PIL import Image, ImageFile, UnidentifiedImageError
from PIL.ExifTags import TAGS, GPSTAGS
from GPSPhoto import gpsphoto
import os

from signals.apps.signals.models.mixins import CreatedUpdatedModel

logger = logging.getLogger(__name__)

# Allow truncated image to be loaded:
ImageFile.LOAD_TRUNCATED_IMAGES = True


class Attachment(CreatedUpdatedModel):
    created_by = models.EmailField(null=True, blank=True)
    _signal = models.ForeignKey(
        "signals.Signal",
        null=False,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    file = models.FileField(
        upload_to='attachments/%Y/%m/%d/',
        null=False,
        blank=False,
        max_length=255
    )
    mimetype = models.CharField(max_length=30, blank=False, null=False)
    is_image = models.BooleanField(default=False)

    class Meta:
        ordering = ('created_at',)
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_image']),
            models.Index(fields=['_signal', 'is_image']),
        ]
        permissions = [
            ('sia_delete_attachment_of_normal_signal', 'Kan bijlage bij standaard melding verwijderen.'),
            ('sia_delete_attachment_of_parent_signal', 'Kan bijlage bij hoofdmelding verwijderen.'),
            ('sia_delete_attachment_of_child_signal',  'Kan bijlage bij deelmelding verwijderen.'),
            ('sia_delete_attachment_of_other_user', 'Kan bijlage bij melding van andere gebruiker verwijderen.'),
            ('sia_delete_attachment_of_anonymous_user', 'Kan bijlage toegevoegd door melder verwijderen.')
        ]

    def _check_if_file_is_image(self):
        try:
            # Open the file with Pillow
            img = Image.open(self.file)
            # print(self.file.path)
            # print(img.getexif())
            # exif_table={}
            # for k, v in img.getexif().items():
            #     tag=TAGS.get(k)
            #     exif_table[tag]=v
            # print(exif_table)
            # gps_info={}
            # for k, v in exif_table['GPSInfo'].items():
            #     geo_tag=GPSTAGS.get(k)
            #     gps_info[geo_tag]=v
            # print(gps_info)
        except UnidentifiedImageError:
            # Raised when Pillow does not recognize an image
            return False
        return True

    def save(self, *args, **kwargs):
        if self.pk is None:
            # Check if file is image
            self.is_image = self._check_if_file_is_image()

            if not self.mimetype and hasattr(self.file.file, 'content_type'):
                self.mimetype = self.file.file.content_type

        super().save(*args, **kwargs)
        print(self.file.path)
        data = gpsphoto.getGPSData(self.file.path)
        print(data)
