from config.configuration import django_service_ip

def django_ip(request):
    return {'DJANGO_IP': django_service_ip}