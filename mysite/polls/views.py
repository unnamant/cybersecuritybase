from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .forms import QuestionForm

from .models import Choice, Question

# Import connection from django.db to execute raw SQL queries (Flaw 3)
# from django.db import connection

# Add the following imports for user authentication and password validation (Flaw 4)
from django.contrib.auth.models import User
# from django.contrib.auth.password_validation import validate_password
# from django.core.exceptions import ValidationError
from .forms import SignupForm

class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')[:5]

class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))

# Here you can find flaw 4
def signup(request):
    error = None
    if request.method == "POST":
        form = SignupForm(request.POST)
        # FLAW 4: A07:2021 – Identification and Authentication Failures
        # The password is accepted without any strength check
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            # FIX 4: Check the password against Django's validators
            # try:
            #     validate_password(password)
            # except ValidationError as e:
            #     error = " ".join(e.messages)
            #     return render(request, "registration/signup.html", {"form": form, "error": error})

            if User.objects.filter(username=username).exists():
                error = "Username already taken."
            else:
                user = User.objects.create_user(username=username, password=password)
                login(request, user)
                return redirect("polls:index")
    else:
        form = SignupForm()
    return render(request, "registration/signup.html", {"form": form, "error": error})

@login_required
def create(request):
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = Question.objects.create(
                question_text=form.cleaned_data["question_text"],
                pub_date=timezone.now(),
                owner=request.user,
            )
            for field in ["choice1", "choice2", "choice3", "choice4"]:
                text = form.cleaned_data[field]
                if text:
                    question.choice_set.create(choice_text=text)
            return redirect("polls:detail", pk=question.id)
    else:
        form = QuestionForm()
    return render(request, "polls/create.html", {"form": form})

@login_required
def my_polls(request):
    questions = Question.objects.filter(owner=request.user).order_by("-pub_date")
    return render(request, "polls/my_polls.html", {"questions": questions})

# Here you can find flaw 1
@login_required
def delete(request, question_id):
    # FLAW 1: A01:2021 – Broken Access Control
    # The flaw is that the delete view does not check if the logged-in user is the owner of the poll before allowing deletion. This could allow any authenticated user to delete any poll, regardless of ownership
    question = get_object_or_404(Question, pk=question_id)
    # FIX 1: Check if the logged-in user is the owner of the poll before allowing deletion
    # question = get_object_or_404(Question, pk=question_id, owner=request.user)
    # Otherwise, if the poll does not belong to the user, return a 404
    if request.method == "POST":
        question.delete()
        return redirect("polls:my_polls")
    return render(request, "polls/delete.html", {"question": question})

# Here you can find flaw 3
def search(request):
    query = request.GET.get("q", "")
    results = []
    if query:
        # FLAW 3: A03:2021 – Injection
        # User input goes straight into the raw SQL, enabling SQL injection.
        results = list(Question.objects.raw(
            f"SELECT * FROM polls_question "
            f"WHERE question_text LIKE '%{query}%'"
        ))

        # FIX 3: Use parameterized queries to prevent SQL injection attacks.
        # results = list(Question.objects.raw(
        #   "SELECT * FROM polls_question WHERE question_text LIKE %s",
        #    ['%' + query + '%'],
        #))


    return render(request, "polls/search.html", {"query": query, "results": results})
