from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponseNotFound


def home_view(request):
    return render(request, 'home.html')


def redirect_404_to_home(request: HttpRequest, exception: Exception) -> HttpResponseNotFound:
    return redirect('home')


