from django.urls import path
from .views import house_list, add_house, add_room

urlpatterns = [
    path('', house_list, name='house_list'),
    path('add/', add_house, name='add_house'),
    path('add-room/', add_room, name='add_room'),
]
