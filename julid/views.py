from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
from trel.models import Complaint
from django.db.models import Count
from julid.helpers import failsafe
from julid import helpers as h
from trel import models as m
from django.db import connection
import os, traceback, logging
import pdb, datetime


class KpiMixin():
    def _get_avg_delta(self, begin_state, end_state, limit):
        total_delta = datetime.timedelta(0)
        count = 0
        for c in m.Complaint.objects.all().order_by('-created_at')[:limit]:
            if not (getattr(c, begin_state) and getattr(c, end_state)): continue
            delta = (getattr(c, begin_state) - getattr(c, end_state))
            total_delta += delta
            count += 1
        logging.info("avg delta, Count: {}".format(count))

        if count == 0:
            return datetime.timedelta(0)
        return (total_delta / count)


class KpiRespond(APIView, KpiMixin):
    permission_classes = (AllowAny,)
    
    def get(self, request):
        limit = int(request.GET.get('limit', 10000))
        avg_delta = self._get_avg_delta('created_at', 'wip_at', limit)
        return HttpResponse(str(avg_delta))


class KpiResolve(APIView, KpiMixin):
    permission_classes = (AllowAny,)
    
    def get(self, request):
        limit = int(request.GET.get('limit', 10000))
        avg_delta = self._get_avg_delta('wip_at', 'resolved_at', limit)
        return HttpResponse(str(avg_delta))



class TotalComplaintPerCategory(APIView):
    permission_classes = (AllowAny,)

    def _get_total_per_cateogory(self):
        complaint_totals = Complaint.objects.all().values('category').annotate(total=Count('category'))
        category_dict = {}
        for complaint_total in complaint_totals:
            category_dict[complaint_total['category']] = complaint_total['total']
        return category_dict
    
    def get(self, request):
        from itertools import groupby
        queryset= Complaint.objects.order_by('category', 'state')
        complaint_dict = {}

        for category, group in groupby(queryset, lambda x: x.category):
            complaint_dict[category] = {}
            for state, inner_group in groupby(group, lambda x: x.state):
                complaint_dict[category][state] = len(list(inner_group))

        complaint_dict['TOTAL'] = self._get_total_per_cateogory()
        return JsonResponse(complaint_dict)



def healthz(request):
    permissions.IsAuthenticated()
    return HttpResponse("OK")