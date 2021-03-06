# -*- coding: utf-8 -*-
import os
import traceback
import zipfile

import exifread
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, HttpResponseRedirect, redirect
from django.urls import reverse, reverse_lazy
from django.utils.timezone import make_aware, is_aware
from django.utils.translation import ugettext as _
from django.views.generic import (
    ListView, UpdateView, CreateView, DeleteView, DetailView
)
from rest_framework import viewsets

from photos import parse_exif_data
from photos.filters import PhotoFilter
from photos.forms import PhotoForm, EventForm
from photos.mixins import ReturnToRefererMixin
from photos.models import Photo, Event, Tag, Import
from usersettings.models import UserSettings
from .serializers import (
    PhotoSerializer, EventSerializer, TagSerializer,
    ImportSerializer, UserSerializer, PhotoEXIFSerializer,
)
from .settings import BASE_DIR


@login_required(login_url='/accounts/login/')
def photolist(request):
    viewtype = request.GET.get('viewtype', None)

    try:
        user_settings = UserSettings.objects.get(user=request.user)
        limit = user_settings.limit
    except UserSettings.DoesNotExist:
        limit = 0

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
            recent = None

        users = User.objects.exclude(id=request.user.id)

        if filter == {} and limit > 0:
            photos = Photo.objects.visible(request.user).distinct()[:limit]
        else:
            photos = Photo.objects.visible(request.user).distinct()
        if viewtype is None:
            photos = PhotoFilter(
                request.GET, queryset=photos, user=request.user
            )
        else:
            if viewtype == 'event':
                order = 'timestamp'
            else:
                order = '-timestamp'
            photos = PhotoFilter(
                request.GET, queryset=photos.order_by(viewtype, order),
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


class SlideshowView(LoginRequiredMixin, ListView):
    model = Photo
    template_name = 'photos/slideshow.html'

    def get_queryset(self):
        idstr = self.request.GET.get('ids')
        ids = idstr.split(',')
        return Photo.objects.filter(id__in=ids).order_by('timestamp')

    def get_context_data(self, **kwargs):
        ctx = super(SlideshowView, self).get_context_data(**kwargs)
        usr_settings = UserSettings.objects.get(user=self.request.user)
        ctx['slide_time'] = usr_settings.slide_time
        return ctx


class PhotoShareView(LoginRequiredMixin, ListView):
    model = Photo
    template_name = 'photos/photo_shares.html'

    def get_queryset(self):
        return Photo.objects.shared(for_user=self.request.user).distinct()


class PhotoMapView(LoginRequiredMixin, ListView):
    model = Photo
    template_name = 'photos/photo_map.html'

    def get(self, request, *args, **kwargs):
        back = request.META.get('HTTP_REFERER', '/photolist/')
        if self.get_queryset().count() == 0:
            messages.warning(
                self.request,
                _('None of the selected photos has location informations')
            )
            return redirect(back)
        return super(PhotoMapView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        idstr = self.request.GET.get('ids')
        ids = idstr.split(',')
        return Photo.objects.filter(
            pk__in=ids,
            longitude__isnull=False,
            latitude__isnull=False
        )

    def get_context_data(self, **kwargs):
        ctx = super(PhotoMapView, self).get_context_data(**kwargs)
        ctx['mapbox_token'] = getattr(settings, "MAPBOX_ACCESS_TOKEN", None)
        return ctx


class PhotoDetailView(LoginRequiredMixin, ReturnToRefererMixin, DetailView):
    model = Photo

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
        ctx['mapbox_token'] = getattr(settings, "MAPBOX_ACCESS_TOKEN", None)
        return ctx


class PhotoDisplayView(LoginRequiredMixin, ReturnToRefererMixin, DetailView):
    model = Photo
    template_name = 'photos/photo_display.html'

    def get_context_data(self, **kwargs):
        ctx = super(PhotoDisplayView, self).get_context_data(**kwargs)
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


class PhotoUpdateView(
    LoginRequiredMixin, ReturnToRefererMixin,
    SuccessMessageMixin, UpdateView):

    model = Photo
    form_class = PhotoForm
    success_message =  _('photo metadata changed.')

    def post(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
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
        event.visible_for.add(request.user)
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
    event_id = request.POST.get('event', None)
    if event_id is None:
        ids = request.POST.getlist('ids[]')
        share = Photo.objects.filter(pk__in=ids)
    else:
        share = Photo.objects.filter(event__id=event_id)
    users = request.POST.getlist('users[]')
    share_to = User.objects.filter(pk__in=users)

    for photo in share:
        if photo.owner in share_to:
            photo.shared.add(*(share_to.exclude(pk=photo.owner.id)))
        else:
            photo.shared.add(*share_to)
        photo.event.visible_for.add(*share_to)

    return HttpResponse('success')


@login_required(login_url='/accounts/login/')
def removeshare(request, photo_id, user_id):
    try:
        photo = Photo.objects.get(pk=photo_id)
        user = User.objects.get(pk=user_id)
        photo.shared.remove(user)
        event = photo.event
        # remove user from event.visible_for if no photos for user shared
        if Photo.objects.filter(event=event, shared=user).count() == 0:
            event.visible_for.remove(user)
    except Photo.DoesNotExist:
        pass
    except:
        traceback.print_exc()
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/accounts/login/')
def removeshareevent(request, event_id, user_id):
    try:
        event = Event.objects.get(pk=event_id)
        user = User.objects.get(pk=user_id)
        for photo in event.photo_set.all():
            photo.shared.remove(user)
        # remove user from event.visible
        event.visible_for.remove(user)
    except Photo.DoesNotExist:
        pass
    except:
        traceback.print_exc()
    return redirect(request.META.get('HTTP_REFERER'))


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


class EventListView(LoginRequiredMixin, ListView):

    model = Event

    def get_queryset(self):
        return Event.objects.filter(visible_for=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.exclude(id=self.request.user.id)
        return context



class EventUpdateView(LoginRequiredMixin, UpdateView):

    model = Event
    form_class = EventForm
    template_name = 'photos/event_form.html'
    success_url = reverse_lazy('eventlist')


class EventCreateView(LoginRequiredMixin, CreateView):

    model = Event
    fields = ['name', ]
    template_name = 'photos/event_form.html'
    success_url = reverse_lazy('eventlist')

    def form_valid(self, form):
        event = form.save()
        event.visible_for.add(self.request.user)
        return super(EventCreateView, self).form_valid(form)


class EventDeleteView(LoginRequiredMixin, DeleteView):

    model = Event
    success_url = reverse_lazy('eventlist')

    def post(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            messages.info(request, _('Delete cancelled'))
            return HttpResponseRedirect(reverse('eventlist'))
        messages.info(request, _('Event deleted'))
        return super(EventDeleteView, self).post(request, *args, **kwargs)


class TagListView(LoginRequiredMixin, ListView):

    model = Tag
    # paginate_by = 100  # if pagination is desired

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['taglist'] = Tag.objects.all()
        return context


class TagUpdateView(LoginRequiredMixin, UpdateView):

    model = Tag
    fields = ['name', ]
    template_name = 'photos/tag_form.html'
    success_url = reverse_lazy('taglist')


class TagCreateView(LoginRequiredMixin, CreateView):

    model = Tag
    fields = ['name', ]
    template_name = 'photos/tag_form.html'
    success_url = reverse_lazy('taglist')


class TagDeleteView(LoginRequiredMixin, DeleteView):

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
    filterset_fields = ['event', 'tags']


class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Events.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filterset_fields = ['name',]


class TagViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Tags.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filterset_fields = ['name', ]


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
