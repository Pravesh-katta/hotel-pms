from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Room


@login_required
def room_list(request):
    rooms = Room.objects.select_related("room_type", "hotel").filter(is_active=True)
    if request.hotel:
        rooms = rooms.filter(hotel=request.hotel)

    status_filter = request.GET.get("status", "")
    type_filter = request.GET.get("type", "")
    if status_filter:
        rooms = rooms.filter(status=status_filter)
    if type_filter:
        rooms = rooms.filter(room_type__name=type_filter)

    room_types = rooms.values_list("room_type__name", flat=True).distinct()

    context = {
        "rooms": rooms,
        "room_types": room_types,
        "current_status": status_filter,
        "current_type": type_filter,
        "status_choices": Room.STATUS_CHOICES,
    }
    return render(request, "dashboard/rooms/list.html", context)


@login_required
def room_status_board(request):
    rooms = Room.objects.select_related("room_type", "hotel").filter(is_active=True)
    if request.hotel:
        rooms = rooms.filter(hotel=request.hotel)

    context = {"rooms": rooms}
    return render(request, "dashboard/rooms/status_board.html", context)


@login_required
def update_room_status(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.hotel and room.hotel != request.hotel:
        return HttpResponse(status=403)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Room.STATUS_CHOICES):
            room.status = new_status
            room.save(update_fields=["status"])

    return render(request, "dashboard/rooms/_room_card.html", {"room": room})
