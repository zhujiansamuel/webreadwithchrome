from student.models import CourseSubscription, StudentInfo, PaymentProcess
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as auth_login
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q

import json
from funtions import *
from .models import *



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
def save_text_function(request):
    note_content = request.POST.get('content')
    note_urls = str(request.POST.get('texturls'))
    note_language = request.POST.get('notelanguage')
    note_title = request.POST.get('notetitle')

    note_expand_contest = note_content
    note_date = timezone.now()
    post_user = request.user
    new_input = Learningtext(user=post_user,
                             online_text=note_content,
                             online_text_url=note_urls,
                             online_text_date=note_date,
                             online_text_expand_contest=note_expand_contest,
                             online_text_title=note_title,
                             online_text_language=note_language)
    new_input.save()
    #-----------------------------------------
    #------------下面要根据语言提问----1205-----
    #-----------------------------------------
    if note_language == "ja":
        rake = Rake()
        story_key = rake.get_keywords(note_expand_contest,3)
        story_text = note_expand_contest

        parsedoc = ParseDocument(story_text, story_key)
        textcontest = Learningtext.objects.get(online_text=note_content)

        parsed_sentences = parsedoc.doc_to_sentences_ja()
        quiz_stem = parsedoc.sentence_select_ja(parsed_sentences)
        stem_key_list = parsedoc.stem_key_select(quiz_stem)
        if stem_key_list:
            for stem_key in stem_key_list:
                    new_question = Quizgenerator(user=post_user,
                                                 textcontest=textcontest,
                                                 text_question=stem_key["stem"],
                                                 text_question_answer=stem_key["correct_key"],
                                                 text_question_type="CLOZE")
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
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))



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
                             online_text_title=note_title,
                             online_text_language=note_language)
    new_input.save()
    #-----------------------------------------
    #------------下面要根据语言提问-----1205-----
    #-----------------------------------------
    if note_language == "ja":
        rake = Rake()
        story_key = rake.get_keywords(note_expand_contest,3)
        story_text = note_expand_contest
        parsedoc = ParseDocument(story_text, story_key)
        textcontest = Learningtext.objects.get(online_text=note_content)
        parsed_sentences = parsedoc.doc_to_sentences_ja()
        quiz_stem = parsedoc.sentence_select_ja(parsed_sentences)
        stem_key_list = parsedoc.stem_key_select(quiz_stem)
        if stem_key_list:
            for stem_key in stem_key_list:
                    new_question = Quizgenerator(user=post_user,
                                                 textcontest=textcontest,
                                                 text_question=stem_key["stem"],
                                                 text_question_answer=stem_key["correct_key"],
                                                 text_question_type="CLOZE")
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
    alltexts = Quizgenerator.objects.filter(user=request.user , test_results="false")

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



def onlinetextpost(request, slug):
    user = request.user
    onlinetext = Learningtext.objects.filter(slug=slug, user=user).first()
    comment = LearningtextLearningnote.objects.filter(onlinetext=onlinetext)
    context = {
        'onlinetext': onlinetext,
        'comment': comment
    }
    return render(request, 'onlinetext/onlinetextpost.html', context)


def onlinetextcomment(request):
    learnnote = request.POST['onlinetextstudynote']
    user = request.user
    postSno = request.POST['onlinetextSno']
    onlinetext = Learningtext.objects.get(id=postSno)

    textcomment = LearningtextLearningnote(learnnote=learnnote, onlinetext=onlinetext)
    textcomment.save()
    messages.success(request, "Comment Added Successfully")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def testsetup(request):
    return render(request, 'onlinetext/testcreater.html')




def testgenerate(request):
    question_number = request.POST.get('questionNo')
    user = request.user
    questions = Quizgenerator.objects.filter(user=user)
    questions = questions.filter(Q(test_results="false") | Q(test_results="null"))
    questions = questions.order_by("?")

    if questions.count() >= int(question_number):

        question = questions[:int(question_number)]
        contest = {
            'question_quiz': question,
        }
    else:
        contest = {
            'question_quiz': questions,
        }
    return render(request, "onlinetext/displayquiz.html", contest)


@csrf_exempt
def answercheck(request):
    answers = request.POST.getlist('answers')
    question_id = request.POST.getlist('questionid')
    testright = 0
    for index,q_id in enumerate(question_id):
        question_in_database = Quizgenerator.objects.filter(id=int(q_id)).first()

        if answers[int(index)] == question_in_database.text_question_answer:
            question_in_database.test_results="true"
            question_in_database.text_question_date=now()
            question_in_database.save()
            testright += 1
        else:
            question_in_database.test_results="false"
            question_in_database.text_question_date = now()
            question_in_database.save()
    result = str(testright) + "/" + str(index+1)
    contest = {
        'result': result,
    }
    return render(request, "onlinetext/testresult.html", contest)
