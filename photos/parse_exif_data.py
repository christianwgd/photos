from datetime import timezone, datetime

import exifread


# based on https://gist.github.com/erans/983821

def _get_if_exist(data, key):
    if key in data:
        return data[key]

    return None


def _convert_to_degress(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to degress in float format
    :param value:
    :type value: exifread.utils.Ratio
    :rtype: float
    """
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)

    return d + (m / 60.0) + (s / 3600.0)


def get_exif_data_as_json(exif_data):
    """
    returns exif_data as json
    :param exif_data:
    :return: json
    """
    exif = dict()
    for tag in exif_data:
        keys = tag.split(' ')
        value = exif_data[tag].__str__()
        main = keys[0]
        if len(keys) == 1:
            sub = 'tag'
        elif len(keys) == 2:
            sub = keys[1]
        elif len(keys) == 3:
            sub = keys[2]
        else:
            main = tag
            sub = 'tag'
        if main not in exif:
            exif[main] = dict()
        exif[main][sub] = value
    return exif


def get_exif_timestamp(exif_data):
    """
    returns exif_data as json
    :param exif_data:
    :return: json
    """
    timestamp = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)

    ts_str = gps_latitude = _get_if_exist(exif_data, 'EXIF DateTimeOriginal')
    timestamp = timezone.make_aware(datetime.datetime.strptime(ts_str, '%Y:%m:%d %H:%M:%S'))
    return timestamp


def get_exif_location(exif_data):
    """
    Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)
    """
    lat = None
    lon = None

    gps_latitude = _get_if_exist(exif_data, 'GPS GPSLatitude')
    gps_latitude_ref = _get_if_exist(exif_data, 'GPS GPSLatitudeRef')
    gps_longitude = _get_if_exist(exif_data, 'GPS GPSLongitude')
    gps_longitude_ref = _get_if_exist(exif_data, 'GPS GPSLongitudeRef')

    if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
        lat = _convert_to_degress(gps_latitude)
        if gps_latitude_ref.values[0] != 'N':
            lat = 0 - lat

        lon = _convert_to_degress(gps_longitude)
        if gps_longitude_ref.values[0] != 'E':
            lon = 0 - lon

    return str(lat), str(lon)
