# -*- coding: utf-8 -*-

import requests
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField
from django.conf import settings


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


class Photo(models.Model):

    class Meta:
        verbose_name = _('photo')
        verbose_name_plural = _('photos')
        ordering = ['-uploaded']

    def __str__(self):
        return self.name

    name = models.CharField(_('name'), max_length=255)
    filename = models.CharField(_('filename'), max_length=255)
    imagefile = models.ImageField(
        _('file'), upload_to='photos/', max_length=255)
    timestamp = models.DateTimeField(_('timestamp'), null=True)
    thumb = models.ImageField(_('thumbnail'), upload_to='photos/thumbnails',
                              max_length=255, null=True, blank=True)
    uploaded_by = models.ForeignKey(User, verbose_name=_(
        'uploaded by'), on_delete=models.PROTECT)
    uploaded = models.DateTimeField(_('uploaded'), auto_now_add=True)
    latitude = models.CharField(_('latitude'), max_length=20, null=True, blank=True)
    longitude = models.CharField(_('longitude'), max_length=20, null=True, blank=True)
    address = JSONField(null=True, blank=True, default=dict())
    exif = JSONField()
    event = models.ForeignKey(Event, models.SET_NULL, blank=True, null=True)
    tags = models.ManyToManyField(Tag)

    def create_thumbnail(self):
        # original code for this method came from
        # http://snipt.net/danfreak/generate-thumbnails-in-django-with-pil/

        # If there is no image associated with this.
        # do not create thumbnail
        if not self.imagefile:
            return

        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        import os
        import io

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


    def save(self, *args, **kwargs):

        if not self.thumb:
            self.create_thumbnail()

        # Bei Verwendung auf anderem Server als wgdnet apiKey Einschränkungen ändern!
        if not self.address:
            google_maps_api_url = \
                'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={key}&language=de'.format(
                    lat=self.latitude,
                    lng=self.longitude,
                    key=settings.GEOPOSITION_GOOGLE_MAPS_API_KEY
                )
            r = requests.get(google_maps_api_url)
            if r.status_code == 200:
                geo_info = r.json()
                results = geo_info['results']
                address = results[0]['address_components']
                formatted = results[0]['formatted_address']
                self.address = {'formatted': formatted, 'address': address}

        force_update = False

        # If the instance already has been saved, it has an id and we set
        # force_update to True
        if self.id:
            force_update = True

        # Force an UPDATE SQL query if we're editing the image to avoid integrity exception
        super(Photo, self, *args, **kwargs).save(force_update=force_update)