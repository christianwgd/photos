# encoding: utf-8
import traceback
import ssl
import certifi
import geopy.geocoders
from geopy import distance, Point


ctx = ssl.create_default_context(cafile=certifi.where())
geopy.geocoders.options.default_ssl_context = ctx


class MapsGeocoder(object):

    def __init__(self, geocoder):
        self.geocoder = geocoder

    def getGeocodeFromAddress(self, address):
        try:
            location = self.geocoder.geocode(address, language='de', timeout=20)
            return (location.latitude, location.longitude)
        except:
            traceback.print_exc()
            return None

    def getAddressFromGeocode(self, lat, lng):
        try:
            position = Point("{}, {}".format(lat, lng))
            address = self.geocoder.reverse(position, language='de', timeout=20)
            return (address)
        except:
            traceback.print_exc()
            return None

    def getDistance(self, latFrom, longFrom, latTo, longTo):
        frm = Point("%s %s" % (latFrom, longFrom))
        to = Point("%s %s" % (latTo, longTo))
        dist = distance.distance(frm,to).kilometers
        return dist
