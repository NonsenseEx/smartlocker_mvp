from django.core.mail import send_mail
from django.conf import settings

def enviar_correo_notificacion(asunto, mensaje, destinatario):
    """
    Función de utilidad para enviar correos. 
    En el MVP, gracias al ConsoleBackend, se imprimirá en la terminal.
    """
    send_mail(
        subject=asunto,
        message=mensaje,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destinatario],
        fail_silently=False,
    )