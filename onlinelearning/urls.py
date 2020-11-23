from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('post-user-text', views.post_text_function, name='PostText'),
    path('login-from-chrome', views.loginfromchrome, name='login-from-chrome'),
    path('login-from-chrome/sucessful', views.loginfromchromevalidation, name='loginfromchromevalidation'),
    path('showonlinetxt', views.showonlinetext, name="showonlinetext"),
    path('showonlinetxtonhome', views.showonlinetextonhome, name="showonlinetextonhome"),


]
