from rest_framework.response import Response

from core.logging_context import get_request_id


def success_response(message: str, status_code: int, data=None, **extra):
    payload = {"success": True, "message": message, "request_id": get_request_id()}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return Response(payload, status=status_code)



def error_response(message: str, status_code: int, errors=None, **extra):
    payload = {"success": False, "message": message, "request_id": get_request_id()}
    if errors is not None:
        payload["errors"] = errors
    payload.update(extra)
    return Response(payload, status=status_code)
