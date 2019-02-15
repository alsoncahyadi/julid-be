from django.http import HttpResponse, JsonResponse
import os, json, traceback, logging

def error_response(code, message):
    message_entry = {
        'code': code,
        'message': message,
        'stack_trace': traceback.format_exc(5).splitlines(),
    }
    logging.error(message_entry)
    return JsonResponse(message_entry, status=code)

def failsafe(text):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                logging.warning("{text} with traceback:\n{traceback}".format(
                    text=text,
                    traceback=traceback.format_exc(5).splitlines()
                    )
                )
                return None
        return wrapper
    return decorator