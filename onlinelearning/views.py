from student.models import CourseSubscription, StudentInfo, PaymentProcess
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as auth_login
import json
from funtions import *
from .models import Learningtext
from .models import Quizgenerator


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


@csrf_exempt
def post_text_function(request):
    #！！！这里需要根据发送规则修改
    auth_key = request.POST.get('authkey')
    note_content = request.POST.get('content')
    note_urls = str(request.POST.get('texturls'))
    note_date = request.POST.get('notedate')
    note_language = request.POST.get('notelanguage')
    note_title = request.POST.get('notetitle')
    #-----回调函数------
    return_json = {'result': "getted"}
    #--------------还没有写，也是用POST得，暂时给一个值------
    note_expand_contest = note_content
    #---------------------------------------------------
    post_student = StudentInfo.objects.get(AuthenticationKey=auth_key)
    id_id = post_student.username_id
    post_user = User.objects.get(id=id_id)

    new_input = Learningtext(user=post_user,
                             online_text=note_content,
                             online_text_url=note_urls,
                             online_text_date=note_date,
                             online_text_expand_contest=note_expand_contest,
                             online_text_title=note_title)
    new_input.save()

    #-----------------------------------------
    #------------下面要根据语言提问--------------
    #-----------------------------------------
    if note_language == "ja":
        #这里产生一个问答，而非填空问题，有一种填空问题的产生方法，但是需要自动产生keyword
        #参考testquizgenerator函数的工作
        qa_generator = QAGeneration()
        results = qa_generator.generate_QA(note_expand_contest)
        textcontest = Learningtext.objects.get(online_text=note_content)
        if results:
            for text_question, text_question_answer in results:
                new_question = Quizgenerator(user=post_user,
                                             textcontest=textcontest,
                                             text_question=text_question,
                                             text_question_answer=text_question_answer,
                                             text_question_type="5W1H")
                new_question.save()





    elif note_language == "en":
        textcontest = Learningtext.objects.get(online_text=note_content)
        questions = generateQuestions(note_expand_contest, 5)
        if questions:
            for question in questions:
                new_question = Quizgenerator(user=post_user,
                                             textcontest=textcontest,
                                             text_question=question["question"],
                                             text_question_answer=question["answer"],
                                             text_question_type="CLOZE")
                new_question.save()
    else:
        #这里可能写入别的语言
        pass
    return HttpResponse(json.dumps(return_json), content_type='application/json')



def showonlinetext(request):
    alltexts = Learningtext.objects.filter(user=request.user)
    context = {'alltexts': alltexts}
    return render(request, 'student/onlinetextdisplay.html', context)


def showonlinetextonhome(request):
    alltexts = Learningtext.objects.filter(user=request.user)
    context = {'alltexts': alltexts}
    return render(request, 'onlinetext/onlinetextonhome.html', context)


@csrf_exempt
def testquizgenerator(request):
    story_text = request.POST.get("story")
    #url实际上是指keyword
    #如果keyword可以自动生成的话，就是我需要的
    story_url = request.POST.get("storyurls")
    story_key = story_url.split()
    parsedoc = ParseDocument(story_text, story_key)

    parsedoc.print_doc()

    parsed_sentences = parsedoc.doc_to_sentences_ja()
    quiz_stem = parsedoc.sentence_select_ja(parsed_sentences)
    stem_key_list = parsedoc.stem_key_select(quiz_stem)
    contest = stem_key_list[0]
    return render(request, 'onlinetext/quizgenerate.html', contest)


def quizpage(request):
    return render(request, 'onlinetext/quizgenerate.html')


def displayquiz(request):
    question_quiz = Quizgenerator.objects.filter(user=request.user)
    contest = {"question_quiz": question_quiz}
    return render(request, "onlinetext/displayquiz.html", contest)
