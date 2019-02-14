from django.contrib.auth.models import User
from rest_framework import viewsets, serializers as s
from django.conf import settings
from django.forms import model_to_dict
from rest_framework import pagination
from rest_framework.response import Response
from rest_framework.fields import SerializerMethodField
from datetime import datetime
from trello.models import *

# Serializer
class ComplaintSerializer(s.ModelSerializer):
  class Meta:
    model = Complaint
    fields = '__all__'


class LogSerializer(s.ModelSerializer):
  class Meta:
    model = Log
    fields = '__all__'


# ViewSet
class ComplaintViewSet(viewsets.ModelViewSet):
  queryset = Complaint.objects.all()
  serializer_class = ComplaintSerializer


class LogViewSet(viewsets.ModelViewSet):
  queryset = Log.objects.all()
  serializer_class = LogSerializer
