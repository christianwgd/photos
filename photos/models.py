# -*- coding: utf-8 -*-
import glob
import os
from datetime import datetime

import pytz
from PIL import Image
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from filebrowser.fields import FileBrowseField
from geopy import Nominatim

from photos import settings
from photos.geocoder import MapsGeocoder
from photos.managers import PhotoVisibleManager, EventVisibleManager


def user_str_patch(self):
    if self.first_name and self.last_name:
        return '{first} {last}'.format(
            first=self.first_name,
            last=self.last_name
        )
    return self.username

User.__str__ = user_str_patch


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
        ordering = ['-timestamp']

    def __str__(self):
        return self.name

    objects = EventVisibleManager()
    timestamp = models.DateTimeField(
        _('timestamp'), auto_created=True, null=True
    )
    name = models.CharField(_('name'), max_length=255)
    visible_for = models.ManyToManyField(
        User, related_name='visisble_for',
        verbose_name=_('Visible for'), blank=True
    )


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
    imagefile = FileBrowseField(
        _('file'), max_length=255,
        extensions=[".jpg", ".jpeg"], blank=True
    )
    timestamp = models.DateTimeField(_('timestamp'), null=True)
    uploaded_by = models.ForeignKey(User, verbose_name=_(
        'uploaded by'), on_delete=models.PROTECT)
    uploaded = models.DateTimeField(_('uploaded'), auto_now_add=True)
    latitude = models.CharField(
        _('latitude'), max_length=20, null=True, blank=True)
    longitude = models.CharField(
        _('longitude'), max_length=20, null=True, blank=True)
    address = models.JSONField(null=True, blank=True, default=dict)
    exif = models.JSONField()
    event = models.ForeignKey(
        Event, models.CASCADE,
        verbose_name=_('event'),
        blank=True, null=True
    )
    upload = models.ForeignKey(
        Import, models.PROTECT,
        verbose_name=_('import'),
        blank=True, null=True
    )
    tags = models.ManyToManyField(Tag, verbose_name=_('tag'), blank=True)
    owner = models.ForeignKey(
        User, verbose_name=_('Owner'),
        on_delete=models.PROTECT, related_name='owner',
    )
    shared = models.ManyToManyField(
        User, related_name='shared_with',
        verbose_name=_('Shared with'), blank=True
    )
    public = models.BooleanField(default=False, verbose_name='Public')

    objects = PhotoVisibleManager()

    def rotate_to_normal(self, orientation):
        image=Image.open(self.imagefile.path)
        thumb=Image.open(self.thumb.path)
        if orientation == 'Rotated 90 CW':
            image=image.rotate(270, expand=True)
            thumb=thumb.rotate(270, expand=True)
            self.exif['Image']['Orientation'] = 'Normal'
            self.save()
        image.save(self.imagefile.path)
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


# @receiver(models.signals.post_save, sender=Photo)
# def rotate_to_normal(sender, instance, **kwargs):
#     if 'Image' in instance.exif:
#         if 'Orientation' in instance.exif['Image']:
#             orientation = instance.exif['Image']['Orientation']
#             instance.rotate_to_normal(orientation)


@receiver(models.signals.post_delete, sender=Photo)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `Photo` object is deleted.
    """
    if instance.imagefile:
        if os.path.isfile(instance.imagefile.path_full):
            new_file_path = os.path.join(
                settings.MEDIA_ROOT, 'trash/', instance.imagefile.name
            )
            if not os.path.exists(os.path.dirname(new_file_path)):
                os.makedirs(os.path.dirname(new_file_path))
            os.rename(instance.imagefile.path_full, new_file_path)

            # remove all related thumbs recursive
            name = ''.join(instance.filename.split('.')[:-1])
            findpath = '{mediapath}/photos/_versions/**/{name}_*.*'.format(
                mediapath = settings.MEDIA_ROOT,
                name = name
            )
            fileList = glob.glob(
                findpath,
                recursive=True
            )
            for filePath in fileList:
                try:
                    os.remove(filePath)
                except OSError:
                    pass

            # remove empty '_versions' dirs
            path = os.path.join(settings.MEDIA_ROOT, 'photos', '_versions')
            for root, dirs, files in os.walk(path, topdown=False):
                for name in dirs:
                    try:
                        # check whether the directory is empty
                        if len(os.listdir( os.path.join(root, name) )) == 0:
                            try:
                                os.rmdir( os.path.join(root, name) )
                            except:
                                pass
                    except:
                        pass
