from django.urls import path

from . import views

urlpatterns = [
    path('', views.playPoker, name='playPoker'),
    path('aiSelect',views.AISelect,name="AISelect"),
    path('skillSelect',views.skillSelect,name="skillSelect"),
]
