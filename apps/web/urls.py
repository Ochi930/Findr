from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("report/", views.report, name="report"),
    path("tip/", views.tip, name="tip"),
    path("hospitals/", views.hospitals, name="hospitals"),
]
