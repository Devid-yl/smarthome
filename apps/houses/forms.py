from django import forms
from .models import House, Room


class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ['name', 'address']


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['house', 'name']
