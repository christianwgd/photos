# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponseRedirect
from django.utils import timezone
from django.contrib import messages
import exifread
import datetime

from photos import parse_exif_data
from photos.models import Photo, Event, Tag


@login_required(login_url='/accounts/login/')
def photolist(request):

    photos = Photo.objects.all()
    return render(request, 'photos/photolist.html', {'photos': photos})


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
        if eventstr != '':
            event, created = Event.objects.get_or_create(name=eventstr)
        tagstr = request.POST.get('tags')
        if tagstr != '':
            tags = tagstr.split(' ')
        else:
            tags = []


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

            photo = Photo(
                name=imgfile.name.split('.')[0],
                filename=imgfile.name,
                imagefile=imgfile,
                timestamp=exif_tsp,
                uploaded_by=request.user,
                exif=exif_json,
                latitude=lat,
                longitude=lon,
                address=dict(),
            )
            if event:
                photo.event = event

            photo.save()
            for tagstr in tags:
                tag = Tag.objects.get(name=tagstr)
                photo.tags.add(tag)

        return HttpResponse('ok')


@login_required(login_url='/accounts/login/')
def settings(request):

    return render(request, 'photos/settings.html', {})
