#!/usr/bin/env python

from google.appengine.ext import ndb


class BaseModel(ndb.Model):

    _serialized_fields = None

    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def all(cls, limit=None):
        return cls.query().order(-cls.created)

    def to_dict(self, exclude=None):

        model_dict = super(BaseModel, self).to_dict(
            include=self._serialized_fields, exclude=exclude)

        id_dict = {'id': self.key.id()}
        return dict(model_dict, **id_dict)

    def __hash__(self):
        return self.key.id()

    def __eq__(self, other):
        return self.key.id() == other.key.id()
