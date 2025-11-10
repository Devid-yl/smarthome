from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import House, Room
from .forms import HouseForm, RoomForm


@login_required
def house_list(request):
    houses = House.objects.filter(owner=request.user)
    return render(request, 'houses/house_list.html', {'houses': houses})


@login_required
def add_house(request):
    if request.method == "POST":
        form = HouseForm(request.POST)
        if form.is_valid():
            house = form.save(commit=False)
            house.owner = request.user
            house.save()
            return redirect('house_list')
    else:
        form = HouseForm()
    return render(request, 'houses/add_house.html', {'form': form})


@login_required
def add_room(request):
    if request.method == "POST":
        form = RoomForm(request.POST)
        form.fields['house'].queryset = House.objects.filter(owner=request.user)
        if form.is_valid():
            form.save()
            return redirect('house_list')
    else:
        form = RoomForm()
        form.fields['house'].queryset = House.objects.filter(owner=request.user)

    return render(request, 'houses/add_room.html', {'form': form})
