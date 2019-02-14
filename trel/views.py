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
from trello.board import Board
from trello.card import Card
from trello.trellolist import List
from julid import helpers as h
from . import models as m
from . import global_variables as g
from . import enums as e
import json
import os, traceback, logging
import pdb, dateutil.parser


# # FOR RAMOS:
# name = 'Test'
# desc = 'Test' # Sekalian tambahin url nya(?) url perlu disimpen kah(?) ato bisa diconstruct dari id(?)
# labels = [e.Label.PENGIRIMAN.value] # from . import enums as e
# position = 'top'
#
# card = client.add_card(name) # add this BEFORE saving to db

def failsafe(text):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                logging.warning(text, traceback.format_exc(5).splitlines())
                return None
        return wrapper
    return decorator

class Webhook(APIView):
    permission_classes = (AllowAny,)
    parser_classes = (JSONParser, FormParser)
    
    def post(self, request):
        try:
            data = request.data
            logging.info(data)
            board = Board.from_json(trello_client=g.trello_client, json_obj=request.data['model'])
            action_type_str = self._get_action_type(data)
            action_type_enum = self._get_enum(e.ActionType, action_type_str)
            if action_type_enum:
                self._map_n_act_n_save_log(action_type_enum, data, board=board)
            logging.info('<LogSaved>')
            return HttpResponse('OK')
        except:
            return h.error_response(500, "Internal server error")


    def get(self, request):
        logging.warning("GET to WEBHOOK with message: {}".format(request.data))
        return HttpResponse('OK')

    # Logging
    def _log_default(self, data, **kwargs):
        return data['action']

    def _log_update_card(self, data, **kwargs):
        board = kwargs.get('board', None)
        list_id = data['action']['display']['entities']['listAfter']['id']
        l = board.get_list(list_id)
        card = Card(l, data['action']['data']['card']['id'])
        card.fetch()

        entry = {
            "actor": data['action']['memberCreator'],
            "action": {
                "type": data['action']['type'],
                "translation_key": data['action']['display']['translationKey'],
            },
            "data": data['action']['data'],
            "complaint": {
                'id': card.id,
                'name': card.name,
                'desc': card.desc,
                'closed': card.closed,
                'url': card.url,
                'shortUrl': card.shortUrl,
                'idMembers': card.idMembers,
                'idShort': card.idShort,
                'idList': card.idList,
                'idBoard': card.idBoard,
                'idLabels': card.idLabels,
                'labels': card._labels,
                'badges': card.badges,
                'pos': card.pos,
                'due': card.due,
                'checked': card.checked,
                'dateLastActivity': card.dateLastActivity,
                'customFields': card._customFields,
                'plugin_data': card._plugin_data,
                'checklists': card._checklists,
                'comments': card._comments,
                'attachments': card._attachments,
            },
        }
        return entry

    # Action
    @failsafe('<ActUpdateCardError>')
    def _act_update_card(self, data, **kwargs):
        translation_key_enum = self._get_enum(e.TranslationKey, data['action']['display']['translationKey'])
        if translation_key_enum == e.TranslationKey.ACTION_MOVE_CARD_FROM_LIST_TO_LIST:
            card_name = data['action']['data']['card']['name']
            list_id = data['action']['display']['entities']['listAfter']['id']
            action_date = dateutil.parser.parse(data['action']['date'])
            # Map Attribute Type
            list_enum = self._get_enum(e.List, list_id)
            attr = {
                e.List.COMPLAINTS: 'ready_at',
                e.List.ON_PROGRESS: 'wip_at',
                e.List.DONE: 'resolved_at',
            }.get(list_enum)
            # Save Complaint
            try:
                complaint = m.Complaint.objects.get(trello_id=1)
                setattr(complaint, attr, action_date)
                complaint.save()
            except m.Complaint.DoesNotExist:
                logging.error("Complaint {} Not Found".format(card_name))
                

    # Mapper
    def _map_n_act_n_save_log(self, enum, data, **kwargs):
        get_log, act = {
            e.ActionType.UPDATE_CARD: (self._log_update_card ,self._act_update_card)
        }.get(enum, (self._log_default, None))

        if act: act(data, **kwargs)
        return g.mongo_logs.insert(get_log(data, **kwargs))

    @failsafe('<ActionTypeNotFound> Log were not saved')
    def _get_action_type(self, data):
        return data['action']['type']

    @failsafe('<GetEnumFailed>')
    def _get_enum(self, Enum, value):
        return Enum(value)
        


def healthz(request):
    permissions.IsAuthenticated()
    return HttpResponse("OK")