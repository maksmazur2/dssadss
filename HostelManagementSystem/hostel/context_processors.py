from .models import Registration


def admin_notifications(request):
    if request.user.is_authenticated and request.user.is_staff:
        qs = (
            Registration.objects
            .select_related('rooms', 'userreg__users')
            .order_by('-postingDate', '-id')[:5]
        )
        return {
            'admin_new_bookings': qs,
            'admin_new_count': Registration.objects.count(),
        }
    return {}
