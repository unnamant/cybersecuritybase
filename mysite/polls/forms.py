from django import forms


class QuestionForm(forms.Form):
    question_text = forms.CharField(max_length=200, label="Question")
    choice1 = forms.CharField(max_length=200, label="Choice 1")
    choice2 = forms.CharField(max_length=200, label="Choice 2")
    choice3 = forms.CharField(max_length=200, label="Choice 3", required=False)
    choice4 = forms.CharField(max_length=200, label="Choice 4", required=False)

