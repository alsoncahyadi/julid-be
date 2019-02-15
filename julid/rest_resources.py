from django.contrib.auth.models import User
from rest_framework import viewsets, mixins, serializers as s
from django.conf import settings
from django.forms import model_to_dict
from rest_framework import pagination
from rest_framework.response import Response
from rest_framework.fields import SerializerMethodField
from datetime import datetime
from trel.models import *
from trel import global_variables as g
from pymongo import ASCENDING, DESCENDING
from bson import json_util
import json

# Serializer
class ComplaintSerializer(s.ModelSerializer):
    class Meta:
        model = Complaint
        fields = '__all__'


class LogSerializer(s.BaseSerializer):
    def to_representation(self, obj):
        return obj

# class LogSerializer(s.ModelSerializer):
#     class Meta:
#         model = Log
#         fields = '__all__'


class MyList(list):
    def count(self):
        len(self)


# ViewSet
class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer


class LogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = LogSerializer
    queryset = MyList([json.loads(json_util.dumps(l)) for l in g.mongo_logs.find().sort([('action_date', DESCENDING), ('_id', DESCENDING)])])
