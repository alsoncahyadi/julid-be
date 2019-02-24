from django.contrib.auth.models import User
from rest_framework import viewsets, mixins, serializers as s
from django.conf import settings
from django.forms import model_to_dict
from rest_framework import pagination
from rest_framework.response import Response
from rest_framework.fields import SerializerMethodField
import dateutil.parser as dp
from trel.models import *
from trel import global_variables as g
from pymongo import ASCENDING, DESCENDING
from bson import json_util
from urllib.parse import parse_qs, urlparse
from django.db.models import Q
import json

# Serializer
class ComplaintSerializer(s.ModelSerializer):
    class Meta:
        model = Complaint
        fields = '__all__'


class LogSerializer(s.BaseSerializer):
    def to_representation(self, obj):
        return obj


# ViewSet
class MyList(list):
    def count(self):
        return len(self) if len(self) else 0


class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.filter(~Q(category__in = ['unknown', 'lainnya']))
    serializer_class = ComplaintSerializer


class ComplaintTimeseriesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ComplaintSerializer
    class Meta:
        ordering = ['-id']
    
    def get_queryset(self):
        queryset = Complaint.objects.all()
        from_date_time = dp.parse(self.request.GET.get('from', ''))
        to_date_time = dp.parse(self.request.GET.get('to', ''))
        category = self.request.GET.get('category', 'all').lower()

        if category == 'all':
            return queryset.filter(created_at__range=(from_date_time, to_date_time)).filter(~Q(category__in = ['unknown', 'lainnya'])).order_by('-id')
        else:
            return queryset.filter(created_at__range=(from_date_time, to_date_time), category=category).order_by('-id')


class LogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = LogSerializer
    queryset = MyList([json.loads(json_util.dumps(l)) for l in g.mongo_logs.find().sort([('action_date', DESCENDING), ('_id', DESCENDING)])])
