from django.http import JsonResponse


def health(request):
    """Endpoint ligero para sondas de disponibilidad del servidor."""
    return JsonResponse({"status": "ok"})
