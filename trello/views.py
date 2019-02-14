from rest_auth.registration.views import LoginView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser, FormParser
from rest_framework import permissions
from django.db import transaction
from django.db import connection
import json
import os, traceback, logging

class Webhook(APIView):
    permission_classes = (AllowAny,)
    parser_classes = (JSONParser, FormParser)

    def post(self, request):
        logging.info(request.data)


def healthz(request):
    permissions.IsAuthenticated()
    return HttpResponse("OK")