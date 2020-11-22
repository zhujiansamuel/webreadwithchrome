from django.shortcuts import render
from student.models import CourseSubscription, StudentInfo, PaymentProcess
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
import json
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as auth_login
from .models import Learningtext


# Create your views here.

def loginfromchromevalidation(request):
    if request.method == 'POST':
        username = request.POST['login_username']
        loginpassword = request.POST['login_password']
        user = authenticate(username=username, password=loginpassword)
        if user is not None:
            auth_login(request,user)
            user_id = User.objects.get(username=username).id
            AuthenticationKey = StudentInfo.objects.get(username_id=user_id).AuthenticationKey
            contest = {
                "username": username,
                "AuthenticationKey": AuthenticationKey,
            }
            #在这里还有返回一个信息告诉控件是谁登录了
            #所以想到先返回一个"恭喜登录成功的页面"->发送用户信息->回到主页
            print(contest)
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
    note_content = request.POST.get('content')
    note_urls = str(request.POST.get('texturls'))
    return_json = {'result': "getted"}





    print(note_content," ===>== ",note_urls)
    return HttpResponse(json.dumps(return_json), content_type='application/json')