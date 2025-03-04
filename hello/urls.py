from django.urls import path
from hello import views

urlpatterns = [
    path("f/<frequency>", views.add_freq, name="add_freq"),
    path("d/<duration>", views.add_dur, name="add_dur"),
    path("s/<slide_duration>", views.add_slide, name="add_slide"),
    path("c", views.clear_data, name="clear_data"),
    path("song", views.fetch_song, name="fetch_song"),
]
