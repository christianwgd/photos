# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Photo, Gallery, Import, Tag


class GallerySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Gallery
        fields = ['url', 'id', 'name']


class TagSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Tag
        fields = ['url', 'id', 'name', ]


class ImportSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Import
        fields = ['url', 'id', 'name', 'timestamp']


class PhotoSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Photo
        fields = [
            'url', 'id', 'name', 'timestamp', 'uploaded',
            'uploaded_by', 'address', 'gallery', 'upload',
            'tags', 'imagefile', 'thumb'
        ]


class PhotoEXIFSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Photo
        fields = ['url', 'id', 'exif']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    full_name = serializers.SerializerMethodField('get_fullname')

    @staticmethod
    def get_fullname(obj):
        return obj.first_name + ' ' + obj.last_name

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'full_name')
