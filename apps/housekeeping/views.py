from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.rooms.models import Room

from .models import HousekeepingTask


@login_required
def housekeeping_board(request):
    tasks = HousekeepingTask.objects.select_related("room", "room__room_type", "hotel", "assigned_to")
    if request.hotel:
        tasks = tasks.filter(hotel=request.hotel)

    pending = tasks.filter(status="pending")
    in_progress = tasks.filter(status="in_progress")
    completed_today = tasks.filter(
        status="completed", completed_at__date=timezone.now().date()
    )

    context = {
        "pending": pending,
        "in_progress": in_progress,
        "completed_today": completed_today,
    }
    return render(request, "dashboard/housekeeping/board.html", context)


@login_required
def update_task_status(request, pk):
    task = get_object_or_404(HousekeepingTask, pk=pk)
    if request.hotel and task.hotel != request.hotel:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status == "in_progress":
            task.status = "in_progress"
            task.assigned_to = request.user
            task.save(update_fields=["status", "assigned_to"])

        elif new_status == "completed":
            task.status = "completed"
            task.completed_at = timezone.now()
            task.save(update_fields=["status", "completed_at"])

            # Mark room as available
            room = task.room
            if room.status == "dirty":
                room.status = "available"
                room.save(update_fields=["status"])

    return render(request, "dashboard/housekeeping/_task_card.html", {"task": task})
