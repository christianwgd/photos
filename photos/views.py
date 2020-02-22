# -*- coding: utf-8 -*-
import io
import json
import os
import zipfile
import exifread
import traceback
from shutil import rmtree

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, JsonResponse, FileResponse
from django.utils.translation import ugettext as _
from django.shortcuts import render, HttpResponseRedirect, redirect
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import User
from django.views.generic import (
    ListView, UpdateView, CreateView, DeleteView, DetailView
)
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.files.storage import FileSystemStorage
from django.utils.timezone import make_aware, is_aware

from photos import parse_exif_data
from photos.models import Photo, Event, Tag, Import
from photos.filters import PhotoFilter
from photos.forms import PhotoForm
from photos.mixins import ReturnToRefererMixin
from usersettings.models import UserSettings

from rest_framework import viewsets
from .serializers import (
    PhotoSerializer, EventSerializer, TagSerializer,
    ImportSerializer, UserSerializer, PhotoEXIFSerializer
)
from .settings import BASE_DIR


@login_required(login_url='/accounts/login/')
def photolist(request):
    viewtype = request.GET.get('viewtype', None)

    filter = {}
    for param in request.GET:
        val = request.GET.get(param, None)
        if len(val) > 0:
            filter[param] = val
    request.session['filter'] = filter

    if request.user.is_authenticated:
        try:
            user_settings = UserSettings.objects.get(user=request.user)
            recent = user_settings.recent
        except UserSettings.DoesNotExist:
            recent = getattr(settings, "DEFAULT_PHOTOS_RECENT", 10)

        users = User.objects.exclude(id=request.user.id)
        photos = Photo.objects.visible(request.user)
        if viewtype is None:
            photos = PhotoFilter(
                request.GET, queryset=photos, user=request.user
            )
        else:
            photos = PhotoFilter(
                request.GET, queryset=photos.order_by(viewtype), 
                user=request.user
            )
    else:
        photos = PhotoFilter(
            request.GET, queryset=Photo.objects.filter(public=True)
        )
        users = User.objects.none()
        recent = 0

    return render(request, 'photos/photolist.html', {
        'photos': photos,
        'users': users,
        'recent': recent,
        'view': viewtype
    })


class PhotoMapView(ListView):
    model = Photo
    template_name = 'photos/photo_map.html'

    def get_queryset(self):
        idstr = self.request.GET.get('ids')
        ids = idstr.split(',')
        return Photo.objects.filter(
            pk__in=ids
        ).exclude(latitude=None).exclude(longitude=None)


class PhotoDetailView(ReturnToRefererMixin, DetailView):
    model = Photo

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(PhotoDetailView, self).get_context_data(**kwargs)
        filter_params = self.request.session.get('filter')
        query_param = ''
        if len(filter_params) > 1:
            c = '?'
            for key, value in filter_params.items():
                query_param += '{}{}={}'.format(c, key, value)
                c = '&'
        ctx['query_param'] = query_param
        return ctx


@login_required(login_url='/accounts/login/')
def new(request):
    return render(request, 'photos/photonew.html', {})


class PhotoUpdateView(ReturnToRefererMixin, SuccessMessageMixin, UpdateView):

    model = Photo
    form_class = PhotoForm
    success_message =  _('photo metadata changed.')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            messages.info(request, 'Funktion abgebrochen.')
            return redirect(self.get_cancel_url())
        return super(PhotoUpdateView, self).post(request, *args, **kwargs)


@login_required(login_url='/accounts/login/')
def imgedit(request, photo_id):

    photo = Photo.objects.get(pk=photo_id)
    return render(request, 'photos/imgedit.html', {'photo': photo})


@login_required(login_url='/accounts/login/')
def delete(request, photo_id):

    try:
        photo = Photo.objects.get(pk=photo_id)
    except Photo.DoesNotExist:
        messages.error(request, _(
            'Photo does not exist.'))
        return HttpResponseRedirect(reverse('photolist'))

    if request.method == 'POST':

        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse('photolist'))

        photo.delete()
        messages.success(request, _(
            'Photo {photo} deleted.').format(photo=photo.name))
        return HttpResponseRedirect(reverse('photolist'))

    return render(request, 'photos/photodelete.html', {'photo': photo})


@login_required(login_url='/accounts/login/')
def fileupload(request):

    if request.method == 'POST':

        upload = Import.objects.create()

        eventstr = request.POST.get('event')
        if eventstr != '':
            event, ev_created = Event.objects.get_or_create(name=eventstr)
        else:
            event, ev_created = Event.objects.get_or_create(name=upload.name)
        tagstr = request.POST.get('tags')
        if tagstr != '':
            tags = tagstr.split(';')
        else:
            tags = []

        count = 0
        files = request.FILES
        for f in files:

            # save file to media directory
            imgfile = files[f]
            fs = FileSystemStorage()
            mediadir = getattr(settings, "MEDIA_ROOT", None)
            filename = os.path.join(mediadir, 'photos', upload.slug, imgfile.name)
            imgfilename = fs.save(filename, imgfile)

            exif_data = exifread.process_file(imgfile, details=False)
            exif_json = parse_exif_data.get_exif_data_as_json(exif_data)
            exif_tsp = parse_exif_data.get_exif_timestamp(exif_data)
            if not is_aware(exif_tsp):
                exif_tsp = make_aware(exif_tsp)
            lat, lon = parse_exif_data.get_exif_location(exif_data)
            if lat is not None and lon is not None:
                lat = '{:3.10}'.format(lat)
                lon = '{:3.10}'.format(lon)

            basename = os.path.basename(imgfilename)
            photo = Photo(
                name=basename.split('.')[0],
                filename=basename,
                timestamp=exif_tsp,
                uploaded_by=request.user,
                owner=request.user,
                exif=exif_json,
                latitude=lat,
                longitude=lon,
                upload=upload,
            )
            if event:
                photo.event = event

            photo.imagefile = os.path.join('photos', upload.slug, basename)
            photo.geocode()
            photo.save()
            count += 1

            for tagstr in tags:
                tag, created = Tag.objects.get_or_create(name=tagstr)
                photo.tags.add(tag)

        messages.success(request, _(
            'successfully added {count} photos.').format(count=count))

        return HttpResponse('ok')

@login_required(login_url='/accounts/login/')
def geocode(request):
    photos = Photo.objects.all()
    count = 0
    for photo in photos:
        if photo.latitude and photo.longitude:
            # address = dict()
            # geoCoder = MapsGeocoder(geocoder=Nominatim())
            # location = geoCoder.getAddressFromGeocode(photo.latitude, photo.longitude)
            # if location is not None:
            #     if len(location) > 0:
            #         loc_str = location.raw['display_name']
            #         address = {'formatted': loc_str, 'address': location.raw}
            #         photo.address = address
            photo.geocode()
            photo.save()
            count += 1
    messages.success(request, _(
        'successfully geocoded {count} photos.').format(count=count))
    return HttpResponseRedirect(reverse('photolist'))


@login_required(login_url='/accounts/login/')
def processdelete(request):
    ids = request.POST.getlist('ids[]')
    delete = Photo.objects.filter(pk__in=ids)
    delete.delete()
    return HttpResponse('success')


@login_required(login_url='/accounts/login/')
def processshare(request):
    ids = request.POST.getlist('ids[]')
    users = request.POST.getlist('users[]')
    share_to = User.objects.filter(pk__in=users)
    share = Photo.objects.filter(pk__in=ids)
    for photo in share:
        if photo.owner in share_to:
            photo.shared.add(*(share_to.exclude(pk=photo.owner.id)))
        else:
            photo.shared.add(*share_to)
    return HttpResponse('success')


@login_required(login_url='/accounts/login/')
def removeshare(request, photo_id, user_id):
    try:
        photo = Photo.objects.get(pk=photo_id)
        user = User.objects.get(pk=user_id)
        photo.shared.remove(user)
    except Photo.DoesNotExist:
        pass
    except:
        traceback.print_exc()
    return redirect(reverse('photodetail', args=(photo_id,)))


@login_required(login_url='/accounts/login/')
def delete_empty(request):

    usedUploads = Photo.objects.all().order_by('upload_id').values('upload_id').distinct('upload_id')
    uploadsToDelete = Import.objects.exclude(pk__in=usedUploads)
    for upload in uploadsToDelete:
        dirname = os.path.abspath('{}/photos/{}'.format(settings.MEDIA_ROOT, upload.slug))
        try:
            rmtree(dirname)
        except:
            traceback.print_exc()
            messages.error(request, _('could not remove directory'))
    uploadsToDelete.delete()

    usedEvents = Photo.objects.all().order_by('event_id').values('event_id').distinct('event_id')
    Event.objects.exclude(pk__in=usedEvents).delete()

    return HttpResponseRedirect(reverse('photolist'))



@login_required(login_url='/accounts/login/')
def processassign(request):
    ids = request.POST.getlist('ids[]')
    evt = request.POST.get('event')
    tgs = request.POST.getlist('tags[]')
    own = request.POST.get('owner')

    if evt:
        event = Event.objects.get(pk=evt)
    else:
        event = None

    if own:
        owner = User.objects.get(pk=own)
    else:
        owner = None

    tags = Tag.objects.filter(pk__in=tgs)
    photos = Photo.objects.filter(pk__in=ids)

    with transaction.atomic():
        for photo in photos:
            if event is not None:
                photo.event = event
            if owner is not None:
                photo.owner = owner
            photo.tags.add(*tags)
            photo.save()

    return HttpResponse('success')


@login_required(login_url='/accounts/login/')
def preparedownload(request):
    ids = request.POST.getlist('ids[]')
    filenames = [photo.imagefile.path_full for photo in Photo.objects.filter(pk__in=ids)]

    try:
        zip_filename = _('photos') + '.zip'
        zip_path = os.path.join(
            BASE_DIR, 'media', 'temp',
        )
        zip_fullpath = os.path.join(zip_path, zip_filename)

        zf = zipfile.ZipFile(zip_fullpath, "w")

        for file_name in filenames:
            zf.write(
                file_name,
                os.path.basename(file_name),
                compress_type=zipfile.ZIP_DEFLATED
            )
        zf.close()
    except:
        traceback.print_exc()

    return HttpResponse('success')


@login_required(login_url='/accounts/login/')
def processdownload(request):
    zip_filename = _('photos') + '.zip'
    zip_path = os.path.join(
        BASE_DIR, 'media', 'temp',
    )
    zip_fullpath = os.path.join(zip_path, zip_filename)
    zip_file = open(zip_fullpath, 'rb')
    resp = FileResponse(zip_file, content_type="application/force-download")
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename
    os.remove(zip_fullpath)
    return resp


class EventListView(ListView):

    model = Event
    # paginate_by = 100  # if pagination is desired

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['eventlist'] = Event.objects.all()
        return context


class EventUpdateView(UpdateView):

    model = Event
    fields = ['name', ]
    template_name = 'photos/event_form.html'
    success_url = reverse_lazy('eventlist')


class EventCreateView(CreateView):

    model = Event
    fields = ['name', ]
    template_name = 'photos/event_form.html'
    success_url = reverse_lazy('eventlist')


class EventDeleteView(DeleteView):

    model = Event
    success_url = reverse_lazy('eventlist')

    def post(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            messages.info(request, _('Delete cancelled'))
            return HttpResponseRedirect(reverse('eventlist'))
        messages.info(request, _('Event deleted'))
        return super(EventDeleteView, self).post(request, *args, **kwargs)


class TagListView(ListView):

    model = Tag
    # paginate_by = 100  # if pagination is desired

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['taglist'] = Tag.objects.all()
        return context


class TagUpdateView(UpdateView):

    model = Tag
    fields = ['name', ]
    template_name = 'photos/tag_form.html'
    success_url = reverse_lazy('taglist')


class TagCreateView(CreateView):

    model = Tag
    fields = ['name', ]
    template_name = 'photos/tag_form.html'
    success_url = reverse_lazy('taglist')


class TagDeleteView(DeleteView):

    model = Tag
    success_url = reverse_lazy('taglist')

    def post(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            messages.info(request, _('Delete cancelled'))
            return HttpResponseRedirect(reverse('taglist'))
        messages.info(request, _('Tag deleted'))
        return super(TagDeleteView, self).post(request, *args, **kwargs)


# REST Views
class PhotoViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Photos.
    """
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer


class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Events.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class TagViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Tags.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ImportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Imports.
    """
    queryset = Import.objects.all()
    serializer_class = ImportSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class PhotoExifViewSet(viewsets.ModelViewSet):
    """
    API endpoint for EXIF-Data.
    """
    queryset = Photo.objects.all()
    serializer_class = PhotoEXIFSerializer
