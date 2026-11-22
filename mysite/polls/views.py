from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import redirect

from .forms import QuestionForm

from .models import Choice, Question

import logging

logger = logging.getLogger(__name__)

# Import connection from django.db to execute raw SQL queries (Flaw 3)
# from django.db import connection

# Add the following imports for user authentication and password validation (Flaw 4)
from django.contrib.auth.models import User
# from django.contrib.auth.password_validation import validate_password
# from django.core.exceptions import ValidationError
from .forms import SignupForm

def is_unlocked(request, question):
    if not question.access_password:
        return True
    return question.id in request.session.get("unlocked_polls", [])

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

def detail(request, pk):
    question = get_object_or_404(Question, pk=pk, pub_date__lte=timezone.now())

    if not is_unlocked(request, question):
        error = None
        if request.method == "POST":
            password = request.POST.get("access_password", "")

            # FLAW 2: The password is compared as plain text.
            correct = password == question.access_password

            # FIX 2: Compare the password against the stored hash.
            # correct = check_password(password, question.access_password)

            if correct:
                unlocked = request.session.get("unlocked_polls", [])
                unlocked.append(question.id)
                request.session["unlocked_polls"] = unlocked
                return redirect("polls:detail", pk=question.id)
            error = "Wrong password."
        return render(request, "polls/password.html", {"question": question, "error": error})

    return render(request, "polls/detail.html", {"question": question})


def results(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if not is_unlocked(request, question):
        return redirect("polls:detail", pk=question.id)
    return render(request, "polls/results.html", {"question": question})

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if not is_unlocked(request, question):
        return redirect("polls:detail", pk=question.id)

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

# Here you can find flaw 2
@login_required
def create(request):
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["access_password"]

            # FLAW 2: A02:2021 – Cryptographic Failures
            # The access password is stored in the database as plain text.
            stored_password = password

            # FIX 2: Store only a salted hash of the password.
            # stored_password = make_password(password) if password else ""

            question = Question.objects.create(
                question_text=form.cleaned_data["question_text"],
                pub_date=timezone.now(),
                owner=request.user,
                access_password=stored_password,
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

# Here you can find flaw 1 and 5
@login_required
def delete(request, question_id):
    # FLAW 1: A01:2021 – Broken Access Control
    # The flaw is that the delete view does not check if the logged-in user is the owner of the poll before allowing deletion. This could allow any authenticated user to delete any poll, regardless of ownership
    question = get_object_or_404(Question, pk=question_id)
    # FIX 1: Check if the logged-in user is the owner of the poll before allowing deletion
    # question = get_object_or_404(Question, pk=question_id, owner=request.user)
    # Otherwise, if the poll does not belong to the user, return a 404
    if request.method == "POST":
        # FLAW 5: A09:2021 – Security Logging and Monitoring Failures
        # Deleting a poll is not logged, so there is no audit trail of who deleted what (destructive action)
        # FIX 5: Log the deletion so suspicious activity can be detected.
        # logger.warning("User %s deleted poll %s", request.user.username, question.id)
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
