# -*- coding: utf-8 -*-
import requests
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponseRedirect
from django.contrib import messages
import exifread

from photos import parse_exif_data
from photos.models import Photo, Event, Tag, Import
from photos.filters import PhotoFilter
from usersettings.models import UserSettings


@login_required(login_url='/accounts/login/')
def photolist(request):

    try:
        settings = UserSettings.objects.get(user=request.user)
        recent = ':{slice}'.format(slice=settings.recent)
    except UserSettings.DoesNotExist:
        recent = ':{slice}'.format(slice=10)

    photos = PhotoFilter(request.GET, queryset=Photo.objects.all())
    return render(request, 'photos/photolist.html', {'photos': photos, 'recent': recent})


@login_required(login_url='/accounts/login/')
def byevent(request):

    photos = PhotoFilter(request.GET, queryset=Photo.objects.all())
    return render(request, 'photos/byevent.html', {'photos': photos})


@login_required(login_url='/accounts/login/')
def byimport(request):

    photos = PhotoFilter(request.GET, queryset=Photo.objects.all().order_by('-upload__timestamp'))
    return render(request, 'photos/byimport.html', {'photos': photos})


@login_required(login_url='/accounts/login/')
def detail(request, photo_id):

    photo = Photo.objects.get(pk=photo_id)
    return render(request, 'photos/photodetail.html', {'photo': photo})


@login_required(login_url='/accounts/login/')
def new(request):

    return render(request, 'photos/photonew.html', {})


@login_required(login_url='/accounts/login/')
def delete(request, photo_id):

    try:
        photo = Photo.objects.get(pk=photo_id)
    except Photo.DoesNotExist:
        messages.error(request, _(
            'Photo does not exist.'))
        return HttpResponseRedirect('/')

    if request.method == 'POST':

        if 'cancel' in request.POST:
            return HttpResponseRedirect('/')

        photo.delete()
        messages.success(request, _(
            'Photo {photo} deleted.').format(photo=photo.name))
        return HttpResponseRedirect('/')

    return render(request, 'photos/photodelete.html', {'photo': photo})


@login_required(login_url='/accounts/login/')
def fileupload(request):

    if request.method == 'POST':

        eventstr = request.POST.get('event')
        tagstr = request.POST.get('tags')
        if tagstr != '':
            tags = tagstr.split(' ')
        else:
            tags = []

        upload, imp_created = Import.objects.get_or_create(
            name=datetime.now().strftime('%Y:%m:%d %H:%M:%S'))

        count = 0
        files = request.FILES
        for f in files:

            imgfile = files[f]

            exif_data = exifread.process_file(imgfile, details=False)
            exif_json = parse_exif_data.get_exif_data_as_json(exif_data)
            exif_tsp = parse_exif_data.get_exif_timestamp(exif_data)
            lat, lon = parse_exif_data.get_exif_location(exif_data)
            if lat is not None and lon is not None:
                lat = '{:3.10}'.format(lat)
                lon = '{:3.10}'.format(lon)

            # Bei Verwendung auf anderem Server als wgdnet apiKey Einschränkungen ändern!
            address = dict()
            google_maps_api_url = \
                'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={key}&language=de'.format(
                    lat=lat,
                    lng=lon,
                    key=settings.GEOPOSITION_GOOGLE_MAPS_API_KEY
                )
            r = requests.get(google_maps_api_url)
            if r.status_code == 200:
                geo_info = r.json()
                results = geo_info['results']
                address = results[0]['address_components']
                formatted = results[0]['formatted_address']
                address = {'formatted': formatted, 'address': address}

            if eventstr != '':
                event, ev_created = Event.objects.get_or_create(name=eventstr)
            else:
                event = None

            photo = Photo(
                name=imgfile.name.split('.')[0],
                filename=imgfile.name,
                imagefile=imgfile,
                timestamp=exif_tsp,
                uploaded_by=request.user,
                exif=exif_json,
                latitude=lat,
                longitude=lon,
                address=address,
                upload=upload,
            )
            if event:
                photo.event = event

            photo.save()
            count += 1

            for tagstr in tags:
                try:
                    tag = Tag.objects.get(name=tagstr)
                    photo.tags.add(tag)
                except Tag.DoesNotExist:
                    pass

        messages.success(request, _(
            'successfully added {count} photos.'.format(count=count)))

        return HttpResponse('ok')


@login_required(login_url='/accounts/login/')
def processdelete(request):
    ids = request.POST.getlist('ids[]')
    delete = Photo.objects.filter(pk__in=ids)
    deleted = delete.count()
    delete.delete()
    return HttpResponse('success')
