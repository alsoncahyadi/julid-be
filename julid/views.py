from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
from julid.helpers import failsafe
from julid import helpers as h
from trel import models as m
import os, traceback, logging
import pdb, datetime


# # FOR RAMOS:
# name = 'Test'
# desc = 'Test' # Sekalian tambahin url nya(?) url perlu disimpen kah(?) ato bisa diconstruct dari id(?)
# labels = [e.Label.PENGIRIMAN.value] # from . import enums as e
# position = 'top'
#
# card = client.add_card(name) # add this BEFORE saving to db

class KpiMixin():
    def _get_avg_delta(self, begin_state, end_state, limit):
        total_delta = datetime.timedelta(0)
        for c in m.Complaint.objects.all()[:limit]:
            if not c.wip.at: continue
            delta = (getattr(c, begin_state) - getattr(c, end_state))
            total_delta += delta if delta > 0 else 0
        return (total_delta / limit)


class KpiRespond(APIView, KpiMixin):
    permission_classes = (AllowAny,)
    
    def get(self, request):
        limit = request.GET.get('limit', 100)
        avg_delta = self._get_avg_delta('created_at', 'wip_at', limit)
        return HttpResponse(str(avg_delta))


class KpiResolve(APIView, KpiMixin):
    permission_classes = (AllowAny,)
    
    def get(self, request):
        limit = request.GET.get('limit', 100)
        avg_delta = self._get_avg_delta('wip_at', 'resolved_at', limit)
        return HttpResponse(str(avg_delta))


def healthz(request):
    permissions.IsAuthenticated()
    return HttpResponse("OK")