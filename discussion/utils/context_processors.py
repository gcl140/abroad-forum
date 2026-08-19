from discussion.models import Notification
from discussion.views import get_online_users


def context_to_extend(request):
    _, online_count, everyone_count = get_online_users()

    user = request.user
    unreadnotificationcount = 0
    if user.is_authenticated:
        unreadnotificationcount = Notification.objects.filter(
            statuses__user=user,
            statuses__is_read=False
        ).count()

    return {
        'online_count': online_count,
        'everyone_count': everyone_count,
        'unreadnotificationcount': unreadnotificationcount,
    }
