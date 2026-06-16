from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("randomPage", views.randomPage, name="randomPage"),
    path("search", views.search, name="search"),
    path("newPage", views.newPage, name="newPage"),
    path("<str:title>", views.entry, name="entry"),
    path("<str:title>/edit", views.editPage, name="editPage"),  # <-- this is required
]

