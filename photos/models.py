# -*- coding: utf-8 -*-
import os
import io
import pytz
from geopy import Nominatim
from datetime import datetime
from PIL import Image

from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField
from django.core.files.uploadedfile import SimpleUploadedFile

from photos import settings
from photos.geocoder import MapsGeocoder


class Import(models.Model):

    class Meta:
        verbose_name = _('import')
        verbose_name_plural = _('imports')
        ordering = ['-timestamp']

    def __str__(self):
        return self.name

    name = models.CharField(_('name'), max_length=255)
    timestamp = models.DateTimeField(_('uploaded'))
    slug = models.CharField(_('slug'), max_length=255)

    def save(self, *args, **kwargs):
        if not self.timestamp:
            tz = pytz.timezone('Europe/Berlin')
            self.timestamp = datetime.now(tz)
        if self.timestamp:
            self.name = self.timestamp.strftime('%d.%m.%Y %H:%M:%S')
            self.slug = self.timestamp.strftime('%Y-%m-%d_%H-%M-%S')
        super(Import, self).save(*args, **kwargs)


class Event(models.Model):

    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')
        ordering = ['name']

    def __str__(self):
        return self.name

    name = models.CharField(_('name'), max_length=255)


class Tag(models.Model):

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ['name']

    def __str__(self):
        return self.name

    name = models.CharField(_('name'), max_length=255)


def photo_path(instance, filename):
    pathname = 'photos/{0}/{1}'.format(instance.upload.slug, filename)
    return pathname


def thumb_path(instance, filename):
    pathname = 'photos/{0}/thumbnails/{1}'.format(
        instance.upload.slug, filename)
    return pathname


class Photo(models.Model):

    class Meta:
        verbose_name = _('photo')
        verbose_name_plural = _('photos')
        ordering = ['-timestamp']

    def __str__(self):
        return self.name

    name = models.CharField(_('name'), max_length=255)
    filename = models.CharField(_('filename'), max_length=255)
    imagefile = models.ImageField(
        _('file'), upload_to=photo_path, max_length=255)
    timestamp = models.DateTimeField(_('timestamp'), null=True)
    thumb = models.ImageField(_('thumbnail'), upload_to=thumb_path,
                              max_length=255, null=True, blank=True)
    uploaded_by = models.ForeignKey(User, verbose_name=_(
        'uploaded by'), on_delete=models.PROTECT)
    uploaded = models.DateTimeField(_('uploaded'), auto_now_add=True)
    latitude = models.CharField(
        _('latitude'), max_length=20, null=True, blank=True)
    longitude = models.CharField(
        _('longitude'), max_length=20, null=True, blank=True)
    address = JSONField(null=True, blank=True, default=dict())
    exif = JSONField()
    event = models.ForeignKey(Event, models.SET_NULL, blank=True, null=True)
    upload = models.ForeignKey(Import, models.PROTECT, blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def create_thumbnail(self):
        # original code for this method came from
        # http://snipt.net/danfreak/generate-thumbnails-in-django-with-pil/

        # If there is no image associated with this.
        # do not create thumbnail
        if not self.imagefile:
            return

        Image.LOAD_TRUNCATED_IMAGES = True

        # Set our max thumbnail size in a tuple (max width, max height)
        THUMBNAIL_SIZE = (200, 200)

        DJANGO_TYPE = self.imagefile.file.content_type

        if DJANGO_TYPE == 'image/jpeg':
            PIL_TYPE = 'jpeg'
            FILE_EXTENSION = 'jpg'
        elif DJANGO_TYPE == 'image/png':
            PIL_TYPE = 'png'
            FILE_EXTENSION = 'png'

        # Open original photo which we want to thumbnail using PIL's Image
        #image = Image.open(io.BytesIO(self.imagefile.read()))
        image = Image.open(self.imagefile)

        # We use our PIL Image object to create the thumbnail, which already
        # has a thumbnail() convenience method that contrains proportions.
        # Additionally, we use file.ANTIALIAS to make the image look better.
        # Without antialiasing the image pattern artifacts may result.
        image.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)

        # Save the thumbnail
        temp_handle = io.BytesIO()
        image.save(temp_handle, PIL_TYPE)
        temp_handle.seek(0)

        # Save image to a SimpleUploadedFile which can be saved into
        # ImageField
        suf = SimpleUploadedFile(os.path.split(self.imagefile.name)[-1],
                                 temp_handle.read(), content_type=DJANGO_TYPE)
        # Save SimpleUploadedFile into image field
        self.thumb.save(
            '{name}_thumbnail.{extension}'.format(
                name=os.path.splitext(suf.name)[0],
                extension=FILE_EXTENSION
            ),
            suf,
            save=False
        )

    def rotate_to_normal(self, orientation):
        image=Image.open(self.imagefile.path)
        thumb=Image.open(self.thumb.path)
        if orientation == 'Rotated 90 CW':
            image=image.rotate(270, expand=True)
            thumb=thumb.rotate(270, expand=True)
        # elif orientation == '':
        #     image=image.rotate(270, expand=True)
        # elif orientation == '':
        #     image=image.rotate(90, expand=True)
        image.save(self.imagefile.path)
        thumb.save(self.thumb.path)
        image.close()
        thumb.close()
    
    def geocode(self):
        if self.latitude and self.longitude:
            address = dict()
            geoCoder = MapsGeocoder(geocoder=Nominatim())
            location = geoCoder.getAddressFromGeocode(self.latitude, self.longitude)
            if location is not None:
                loc_str = location.raw['display_name']
                address = {'formatted': loc_str, 'address': location.raw}
                self.address = address

    def save(self, *args, **kwargs):

        if not self.thumb:
            self.create_thumbnail()

        force_update = False

        # If the instance already has been saved, it has an id and we set
        # force_update to True
        if self.id:
            force_update = True

        # Force an UPDATE SQL query if we're editing the image to avoid integrity exception
        super(Photo, self, *args, **kwargs).save(force_update=force_update)


@receiver(models.signals.post_save, sender=Photo)
def rotate_to_normal(sender, instance, **kwargs):
    if 'Image' in instance.exif:
        if 'Orientation' in instance.exif['Image']:
            orientation = instance.exif['Image']['Orientation']
            instance.rotate_to_normal(orientation)


@receiver(models.signals.post_delete, sender=Photo)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `Photo` object is deleted.
    """
    if instance.imagefile:
        if os.path.isfile(instance.imagefile.path):
            new_file_path = os.path.join(settings.MEDIA_ROOT, 'trash/', instance.imagefile.name)
            new_thumb_path = os.path.join(settings.MEDIA_ROOT, 'trash/', instance.thumb.name)

            if not os.path.exists(os.path.dirname(new_file_path)):
                os.makedirs(os.path.dirname(new_file_path))

            if not os.path.exists(os.path.dirname(new_thumb_path)):
                os.makedirs(os.path.dirname(new_thumb_path))

            #os.remove(instance.file.path)
            os.rename(instance.imagefile.path, new_file_path)
            os.rename(instance.thumb.path, new_thumb_path)
