import json
import datetime

from google.appengine.ext.ndb import Key
from google.appengine.ext.ndb import GeoPt
from model.base import BaseModel


class JsonSerializer(json.JSONEncoder):

    def default(self, obj):

        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%SZ")

        elif isinstance(obj, Key):
            return obj.id()

        elif isinstance(obj, BaseModel):
            return obj.to_dict()

        elif isinstance(obj, GeoPt):
            return {'lat': obj.lat, 'lon': obj.lon}

        return json.JSONEncoder.default(self, obj)
