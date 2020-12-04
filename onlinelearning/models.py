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


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        #-----------------------------------------
        #------------下面要根据语言提问--------------
        #-----------------------------------------
        if self.online_text_language == "ja":
            #这里产生一个问答，而非填空问题，有一种填空问题的产生方法，但是需要自动产生keyword
            #参考testquizgenerator函数的工作
            qa_generator = QAGeneration()
            results = qa_generator.generate_QA(self.online_text_expand_contest)
            textcontest = self.online_text_expand_contest
            user = self.user
            if results:
                for text_question, text_question_answer in results:
                    new_question = Quizgenerator(user=user,
                                                 textcontest=textcontest,
                                                 text_question=text_question,
                                                 text_question_answer=text_question_answer,
                                                 text_question_type="5W1H")
                    new_question.save()
        elif self.online_text_language == "en":
            textcontest = self.online_text_expand_contest
            questions = generateQuestions(textcontest, 5)
            user = self.user
            if questions:
                for question in questions:
                    new_question = Quizgenerator(user=user,
                                                 textcontest=textcontest,
                                                 text_question=question["question"],
                                                 text_question_answer=question["answer"],
                                                 text_question_type="CLOZE")
                    new_question.save()
        else:
            #这里可能写入别的语言
            pass


class Quizgenerator(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    textcontest = models.ForeignKey(Learningtext, on_delete=models.CASCADE)
    text_question = models.TextField(default="no text_question")
    text_question_answer = models.TextField(default="no text_question_answer")
    text_question_type = models.TextField(default="cloze")
    #key-words
    text_key_word = models.TextField(default="null")
