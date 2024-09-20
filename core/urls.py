from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("accounts/profile/", views.profile, name="profile"),
    path("placements/", views.placements, name="placements"),
    path("analytics/", views.analytics, name="analytics"),
    path("create-placement/", views.create_placement, name="create_placement"),
    path("delete-placement/<int:placement_id>/", views.delete_placement, name="delete_placement"),
    path("editor/<int:placement_id>/", views.placement_editor, name="placement_editor"),
    path('editor/<int:placement_id>/save-changes/', views.save_changes, name='save_changes'),
    path('editor/<int:placement_id>/publish/', views.publish_placement, name='publish_placement'),
    path("proxy/", views.proxy_view, name="proxy_view"),
    path('generate_html/', views.generate_html, name='generate_html'),
    path("get-placement-data/<int:placement_id>/", views.get_placement_data, name="get_placement_data"),
    path('track-event/<int:placement_id>/', views.track_event, name='track_event'),
]
