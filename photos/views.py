# -*- coding: utf-8 -*-
from datetime import datetime
import os
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
from django.shortcuts import render, HttpResponseRedirect, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import formats
from django.utils.http import urlencode
from django.utils.timezone import make_aware, is_aware
from django.utils.translation import gettext as _
from django.views.generic import (
    ListView, UpdateView, CreateView, DeleteView, DetailView
)
from django_filters.views import FilterView
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from photos import parse_exif_data
from photos.filters import PhotoFilter
from photos.forms import PhotoForm, GalleryForm
from photos.mixins import ReturnToRefererMixin
from photos.models import Photo, Gallery, Tag, Import
from usersettings.models import UserSettings
from .serializers import (
    PhotoSerializer, GallerySerializer, TagSerializer,
    ImportSerializer, UserSerializer,
)
from .settings import BASE_DIR


def str_is_date(date_str):
    try:
        return bool(datetime.strptime(date_str, "%Y-%m-%d"))
    except ValueError:
        return False


def date_from_str(date_str):
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return formats.date_format(dt, 'SHORT_DATE_FORMAT')


def photos_cache(request):
    params = {}
    for attr in PhotoFilter.Meta.fields:
        if attr in request.session:
            params[attr] = request.session[attr]
        if 'order' in request.session:
            params['order'] = request.session['order']

    if 'page' in request.session:
        params['page'] = request.session['page']
    return redirect(f"{reverse('photolist')}?{urlencode(params)}")


def reset_cache(request):
    for attr in PhotoFilter.Meta.fields:
        if attr in request.session:
            del request.session[attr]
            request.session.modified = True
        if 'order' in request.session:
            del request.session['order']
            request.session.modified = True
        if 'page' in request.session:
            del request.session['page']
            request.session.modified = True

    return redirect(reverse('photolist'))


def get_string_from_query_dict(params):
    names = {
        'gallery': _('gallery'),
        'tags': _('tags'),
        'timestamp_min': _('timestamp_min'),
        'timestamp_max': _('timestamp_max'),
        'uploaded_min': _('uploaded_min'),
        'uploaded_max': _('uploaded_max'),
        'uploaded_by': _('uploaded_by'),
        'upload': _('import'),
        'order': _('Order'),
    }
    query_string = []
    params = dict(params)
    for item in params:
        if item not in names:
            continue
        value = params.get(item)
        if value[0] == '':
            continue
        if len(value) == 1 and value[0] != '':
            value = value[0]
            if str_is_date(value):
                query_string.append((f'{names[item]}: {date_from_str(value)}', item))
            elif item == 'gallery':
                name = Gallery.objects.get(pk=int(value)).name
                query_string.append((f'{names[item]}: {name}', item))
            elif item == 'upload':
                name = Import.objects.get(pk=int(value)).name
                query_string.append((f'{names[item]}: {name}', item))
            elif item == 'uploaded_by':
                name = User.objects.get(pk=int(value)).get_full_name()
                query_string.append((f'{names[item]}: {name}', item))
            elif item == 'order':
                query_string.append((f'{names[item]}: {_(value)}', item))
            elif item == 'tags':
                name = Tag.objects.get(pk=int(value)).name
                query_string.append((f'{names[item]}: {name}', item))
            else:
                query_string.append((f'{names[item]}: {value}', item))
        else:
            if item == 'tags':
                tag_name_list = list(Tag.objects.filter(pk__in=value).values_list('name', flat=True))
                query_string.append((f'{names[item]}: {", ".join(tag_name_list)}', item))
            else:
                pass
    return query_string


# TODO: Write filter params to session to keep the
#       filter until modified or resettet
class PhotoFilterView(LoginRequiredMixin, FilterView):
    model = Photo
    filterset_class = PhotoFilter

    def get_paginate_by(self, queryset):
        if self.request.user.is_authenticated:
            return self.request.user.usersettings.photos_per_page
        return 12

    def get(self, request, *args, **kwargs):
        request.session['page'] = request.GET.get('page', 1)
        for attr in PhotoFilter.Meta.fields:
            if attr in request.GET and request.GET[attr] != '':
                request.session[attr] = request.GET[attr]
            if 'order' in request.GET:
                request.session['order'] = request.GET['order']
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super().get_context_data(object_list=None, **kwargs)
        ctx['query'] = get_string_from_query_dict(self.request.GET)
        ctx['users'] = User.objects.exclude(id=self.request.user.id)
        return ctx

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Photo.objects.visible(self.request.user).distinct()
        return Photo.objects.none()


class PhotosBy(FilterView):
    model = Photo
    filterset_class = PhotoFilter
    template_name = 'photos/photos_by.html'

    def get_paginate_by(self, queryset):
        return self.request.user.usersettings.photos_per_page

    def get_context_data(self, *, object_list=None, **kwargs):
        ctx = super().get_context_data(object_list=None, **kwargs)
        ctx['property'] = self.kwargs.get('property', 'gallery')
        return ctx

    def get_queryset(self):
        prop = self.kwargs.get('property', 'gallery')
        return Photo.objects.visible(self.request.user).distinct().order_by(prop)


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
        ctx['mapbox_token'] = getattr(settings, "MAPBOX_ACCESS_TOKEN", None)
        return ctx


class PhotoDisplayView(LoginRequiredMixin, ReturnToRefererMixin, DetailView):
    model = Photo
    template_name = 'photos/photo_display.html'


@login_required(login_url='/accounts/login/')
def new(request):
    return render(request, 'photos/photonew.html', {})


class PhotoUpdateView(
    LoginRequiredMixin, ReturnToRefererMixin,
    SuccessMessageMixin, UpdateView
):
    model = Photo
    form_class = PhotoForm
    success_message = _('photo metadata changed.')

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
            return HttpResponseRedirect(reverse('PhotoFilterView'))

        photo.delete()
        messages.success(request, _(
            'Photo {photo} deleted.').format(photo=photo.name))
        return HttpResponseRedirect(reverse('photolist'))

    return render(request, 'photos/photodelete.html', {'photo': photo})


@login_required(login_url='/accounts/login/')
def fileupload(request):
    if request.method == 'POST':

        upload = Import.objects.create()

        gallery_str = request.POST.get('gallery')
        if gallery_str != '':
            gallery, ev_created = Gallery.objects.get_or_create(name=gallery_str)
        else:
            gallery, ev_created = Gallery.objects.get_or_create(name=upload.name)
        gallery.visible_for.add(request.user)
        tag_str = request.POST.get('tags')
        if tag_str != '':
            tags = tag_str.split(';')
        else:
            tags = []

        count = 0
        files = request.FILES
        for f in files:

            # save file to media directory
            imgfile = files[f]
            fs = FileSystemStorage()
            filename = os.path.join('photos', upload.slug, imgfile.name)
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
            if gallery:
                photo.gallery = gallery

            photo.imagefile = os.path.join('photos', upload.slug, basename)
            photo.geocode()
            photo.save()
            count += 1

            for tag_str in tags:
                tag, created = Tag.objects.get_or_create(name=tag_str)
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
            photo.geocode()
            photo.save()
            count += 1
    messages.success(request, _(
        'successfully geocoded {count} photos.').format(count=count))
    return HttpResponseRedirect(reverse('photolist'))


@login_required(login_url='/accounts/login/')
def processdelete(request):
    ids = request.POST.getlist('ids[]')
    Photo.objects.filter(pk__in=ids).delete()
    return HttpResponse('success')


@login_required(login_url='/accounts/login/')
def processshare(request):
    gallery_id = request.POST.get('gallery', None)
    if gallery_id is None:
        ids = request.POST.getlist('ids[]')
        share = Photo.objects.filter(pk__in=ids)
    else:
        share = Photo.objects.filter(gallery__id=gallery_id)
    users = request.POST.getlist('users[]')
    share_to = User.objects.filter(pk__in=users)

    for photo in share:
        if photo.owner in share_to:
            photo.shared.add(*(share_to.exclude(pk=photo.owner.id)))
        else:
            photo.shared.add(*share_to)
        photo.gallery.visible_for.add(*share_to)

    return HttpResponse('success')


@login_required(login_url='/accounts/login/')
def removeshare(request, photo_id, user_id):
    try:
        photo = Photo.objects.get(pk=photo_id)
        user = User.objects.get(pk=user_id)
        photo.shared.remove(user)
        gallery = photo.gallery
        # remove user from gallery.visible_for if no photos for user shared
        if Photo.objects.filter(gallery=gallery, shared=user).count() == 0:
            gallery.visible_for.remove(user)
    except Photo.DoesNotExist:
        pass
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/accounts/login/')
def remove_share_gallery(request, gallery_id, user_id):
    try:
        gallery = Gallery.objects.get(pk=gallery_id)
        user = User.objects.get(pk=user_id)
        for photo in gallery.photo_set.all():
            photo.shared.remove(user)
        # remove user from gallery.visible
        gallery.visible_for.remove(user)
    except Photo.DoesNotExist:
        pass
    return redirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/accounts/login/')
def processassign(request):
    ids = request.POST.getlist('ids[]')
    evt = request.POST.get('gallery')
    tgs = request.POST.getlist('tags[]')
    own = request.POST.get('owner')

    if evt:
        gallery = Gallery.objects.get(pk=evt)
    else:
        gallery = None

    if own:
        owner = User.objects.get(pk=own)
    else:
        owner = None

    tags = Tag.objects.filter(pk__in=tgs)
    photos = Photo.objects.filter(pk__in=ids)

    with transaction.atomic():
        for photo in photos:
            if gallery is not None:
                photo.gallery = gallery
            if owner is not None:
                photo.owner = owner
            photo.tags.add(*tags)
            photo.save()

    return HttpResponse('success')


@login_required(login_url='/accounts/login/')
def preparedownload(request):
    ids = request.POST.getlist('ids[]')
    filenames = [photo.imagefile.path_full for photo in Photo.objects.filter(pk__in=ids)]

    zip_filename = _('photos') + '.zip'
    zip_path = os.path.join(BASE_DIR, 'media', 'temp')
    zip_fullpath = os.path.join(zip_path, zip_filename)

    zf = zipfile.ZipFile(zip_fullpath, "w")

    for file_name in filenames:
        zf.write(
            file_name,
            os.path.basename(file_name),
            compress_type=zipfile.ZIP_DEFLATED
        )
    zf.close()

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


class GalleryListView(LoginRequiredMixin, ListView):
    model = Gallery

    def get_queryset(self):
        return Gallery.objects.filter(visible_for=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.exclude(id=self.request.user.id)
        return context


class GalleryUpdateView(LoginRequiredMixin, UpdateView):
    model = Gallery
    form_class = GalleryForm
    template_name = 'photos/gallery_form.html'
    success_url = reverse_lazy('gallerylist')


class GalleryCreateView(LoginRequiredMixin, CreateView):
    model = Gallery
    fields = ['name', ]
    template_name = 'photos/gallery_form.html'
    success_url = reverse_lazy('gallerylist')

    def form_valid(self, form):
        gallery = form.save()
        gallery.visible_for.add(self.request.user)
        return super(GalleryCreateView, self).form_valid(form)


class GalleryDeleteView(LoginRequiredMixin, DeleteView):
    model = Gallery
    success_url = reverse_lazy('gallerylist')

    def post(self, request, *args, **kwargs):
        if 'cancel' in request.POST:
            messages.info(request, _('Delete cancelled'))
            return HttpResponseRedirect(reverse('gallerylist'))
        messages.info(request, _('Gallery deleted'))
        return super(GalleryDeleteView, self).post(request, *args, **kwargs)


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
    filterset_fields = ['gallery', 'tags']


class GalleryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for galleries.
    """
    queryset = Gallery.objects.all()
    serializer_class = GallerySerializer
    filterset_fields = ['name', ]


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

    @action(methods=['get'], detail=False, url_path=r'username/(?P<username>\w+)')
    def get_user_by_username(self, request, username):
        user = get_object_or_404(User, username=username)
        data = UserSerializer(user, context={'request': request}).data
        return Response(data, status=status.HTTP_200_OK)


# class PhotoExifViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint for EXIF-Data.
#     """
#     queryset = Photo.objects.all()
#     serializer_class = PhotoEXIFSerializer
