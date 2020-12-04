from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from funtions import *

# Create your models here.
class Learningtext(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    online_text = models.TextField()
    online_text_url = models.TextField()
    online_text_date = models.DateTimeField(default=now)
    online_text_expand_contest = models.TextField(default=online_text)
    online_text_title = models.TextField(default="title null")
    online_text_language = models.TextField(default="en")




class Quizgenerator(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    textcontest = models.ForeignKey(Learningtext, on_delete=models.CASCADE)
    text_question = models.TextField(default="no text_question")
    text_question_answer = models.TextField(default="no text_question_answer")
    text_question_type = models.TextField(default="cloze")
    #key-words
    text_key_word = models.TextField(default="null")
