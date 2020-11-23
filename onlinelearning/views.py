from django.shortcuts import render
from student.models import CourseSubscription, StudentInfo, PaymentProcess
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
import json
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as auth_login
from funtions import *
from .models import Learningtext


# Create your views here.

def loginfromchromevalidation(request):
    if request.method == 'POST':
        username = request.POST['login_username_home']
        loginpassword = request.POST['login_password_home']
        users = authenticate(username=username, password=loginpassword)
        if users is not None:
            auth_login(request, users)
            user_id = User.objects.get(username=username).id
            AuthenticationKey = StudentInfo.objects.get(username_id=user_id).AuthenticationKey
            contest = {
                "username": username,
                "AuthenticationKey": AuthenticationKey,
            }
            return render(request, 'successfulLoginFromChrome.html', {'data': contest})
        else:
            return render(request, 'login_chrome.html')
    return redirect('home')


def loginfromchrome(request):
    return render(request, 'login_chrome.html')


#这里还没有保存到数据库
@csrf_exempt
def post_text_function(request):
    #！！！这里需要根据发送规则修改
    #还没有修改！！！！！！
    auth_key = request.POST.get('authkey')
    note_content = request.POST.get('content')
    note_urls = str(request.POST.get('texturls'))
    note_date = request.POST.get('')
    return_json = {'result': "getted"}

    text_question = generate_key(16)
    text_question_answer = generate_key(3)


    post_student=StudentInfo.objects.get(AuthenticationKey=auth_key)
    id_id=post_student.username_id
    post_user = User.objects.get(id=id_id)


    new_input = Learningtext(user=post_user,online_text=note_content,online_text_url=note_urls,text_question=text_question,text_question_answer=text_question_answer)
    new_input.save()


    print(new_input.user,new_input.online_text)
    return HttpResponse(json.dumps(return_json), content_type='application/json')


def showonlinetext(request):
    alltexts = Learningtext.objects.filter(user=request.user)
    context = {'alltexts': alltexts}
    return render(request, 'student/onlinetextdisplay.html', context)

def showonlinetextonhome(request):

    alltexts = Learningtext.objects.filter(user=request.user)
    context = {'alltexts': alltexts}
    return render(request, 'onlinetext/onlinetextonhome.html', context)