from collections import defaultdict
import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404
import requests
from groq import Groq
from django.conf import settings

from .models import Placement, PlacementAnalytics


@login_required
def index(request):
    return render(request, "index.html")


@login_required
def profile(request):
    return render(request, "profile.html")


@login_required
def placements(request):
    placements = Placement.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "placements.html", {"placements": placements})


@login_required
def analytics(request):

    placements = Placement.objects.filter(user=request.user).order_by("-created_at")

    structured_analytics = []

    for placement in placements:

        # Get analytics for the current placement

        analytics_data = PlacementAnalytics.objects.filter(placement=placement)

        # Initialize dictionaries to hold counts over time
        views_by_country = defaultdict(int)
        clicks_by_country = defaultdict(int)
        views_by_referrer = defaultdict(int)
        clicks_by_referrer = defaultdict(int)
        views_by_browser = defaultdict(int)
        clicks_by_browser = defaultdict(int)
        views_by_os = defaultdict(int)
        clicks_by_os = defaultdict(int)
        views_over_time = defaultdict(int)
        clicks_over_time = defaultdict(int)
        for analytic in analytics_data:
            timestamp = analytic.created_at.strftime("%Y-%m-%d")  # Group by day
            event_data = analytic.event_data
            if analytic.event_type == "view":
                views_by_country[event_data.get("country", "Unknown")] += 1
                views_by_referrer[event_data.get("referrer", "Unknown")] += 1
                views_by_browser[event_data.get("browser", "Unknown")] += 1
                views_by_os[event_data.get("os", "Unknown")] += 1
                views_over_time[timestamp] += 1
            elif analytic.event_type == "click":
                clicks_by_country[event_data.get("country", "Unknown")] += 1
                clicks_by_referrer[event_data.get("referrer", "Unknown")] += 1
                clicks_by_browser[event_data.get("browser", "Unknown")] += 1
                clicks_by_os[event_data.get("os", "Unknown")] += 1
                clicks_over_time[timestamp] += 1

        structured_analytics.append(
            {
                "placement": placement,
                "views_by_country": dict(views_by_country),
                "clicks_by_country": dict(clicks_by_country),
                "views_by_referrer": dict(views_by_referrer),
                "clicks_by_referrer": dict(clicks_by_referrer),
                "views_by_browser": dict(views_by_browser),
                "clicks_by_browser": dict(clicks_by_browser),
                "views_by_os": dict(views_by_os),
                "clicks_by_os": dict(clicks_by_os),
                "views_over_time": dict(views_over_time),
                "clicks_over_time": dict(clicks_over_time),
                "views_by_country_json": json.dumps(dict(views_by_country)),
                "clicks_by_country_json": json.dumps(dict(clicks_by_country)),
                "views_by_referrer_json": json.dumps(dict(views_by_referrer)),
                "clicks_by_referrer_json": json.dumps(dict(clicks_by_referrer)),
                "views_by_browser_json": json.dumps(dict(views_by_browser)),
                "clicks_by_browser_json": json.dumps(dict(clicks_by_browser)),
                "views_by_os_json": json.dumps(dict(views_by_os)),
                "clicks_by_os_json": json.dumps(dict(clicks_by_os)),
                "views_over_time_json": json.dumps(dict(views_over_time)),
                "clicks_over_time_json": json.dumps(dict(clicks_over_time)),
            }
        )
    context = {"structured_analytics": structured_analytics}

    return render(request, "analytics.html", context)


@login_required
@require_POST
def create_placement(request):
    page_url = request.POST.get("page_url")
    if not page_url:
        messages.error(request, "page_url is required")
        return redirect("index")

    placement = Placement.objects.create(user=request.user, page_url=page_url, data="")
    return redirect(reverse("placement_editor", args=[placement.id]))


@login_required
def delete_placement(request, placement_id):
    placement = get_object_or_404(Placement, id=placement_id, user=request.user)
    placement.delete()
    return redirect("placements")


@csrf_exempt
@require_POST
@login_required
def save_changes(request, placement_id):
    try:
        placement = Placement.objects.get(id=placement_id, user=request.user)
        data = json.loads(request.body)

        placement.data = data
        placement.save()

        return JsonResponse({"message": "Data saved successfully"}, status=200)
    except Placement.DoesNotExist:
        return JsonResponse({"error": "Placement not found"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)


client = Groq(api_key=settings.GROQ_KEY)

@csrf_exempt
@require_POST
@login_required
def generate_html(request):
    prompt = request.POST.get("prompt", None)
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {
                "role": "system",
                "content": "You are a html expert. when something is asked you only return html with inline css in the element with style property. Minimal good looking code. No extra text only html. If vibrant said then use dark high contrast colors like black white, violet, pink.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )
    html_content = completion.choices[0].message.content
    return JsonResponse({"html": html_content})


@login_required
def publish_placement(request, placement_id):
    placement = get_object_or_404(Placement, id=placement_id, user=request.user)
    return render(request, "publish_placement.html", {"placement": placement})


def get_placement_data(request, placement_id):
    placement = get_object_or_404(Placement, id=placement_id)
    data = json.dumps(placement.data)
    return JsonResponse({"page_url": placement.page_url, "data": data})


@csrf_exempt
@require_POST
def track_event(request, placement_id):
    placement = get_object_or_404(Placement, id=placement_id)
    try:
        data = json.loads(request.body)
        event_type = data.get("event")
        event_data = data.get("eventData", {})

        PlacementAnalytics.objects.create(
            placement=placement, event_type=event_type, event_data=event_data
        )

        return JsonResponse({"message": "Analytics data recorded"}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)


@login_required
def placement_editor(request, placement_id):
    placement = get_object_or_404(Placement, id=placement_id, user=request.user)
    return render(request, "editor.html", {"placement": placement})


@csrf_exempt
@login_required
def proxy_view(request):
    target_url = request.GET.get("targetUrl")
    response = requests.get(target_url)
    return HttpResponse(
        response.content,
        status=response.status_code,
        content_type=response.headers.get("Content-Type", "text/plain"),
    )
