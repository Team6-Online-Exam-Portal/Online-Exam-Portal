from django.contrib import admin
from .models import Question, Option, Exam, ExamQuestion

admin.site.register(Question)
admin.site.register(Option)
admin.site.register(Exam)
admin.site.register(ExamQuestion)