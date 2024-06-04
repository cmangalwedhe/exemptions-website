from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from exemptions.models import Exemption
from django.http import HttpResponse
from exemptions.models import StringsList
from django.contrib import messages


# Create your views here.
def home(request):
    if request.method == "POST":
        student_id = int(request.POST["id"])
        student_model = Exemption.objects.get_or_create(identifier=student_id)[0]
        string = StringsList.objects.create(value="Computer Science III K")
        student_model.exempted_strings.add(string)
        return render(request, "table.html", {"courses": [course.value for course in student_model.exempted_strings.all()], "model": student_model})

    return render(request,  "base.html")


def teacher(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return teacher_list(request)
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")


def teacher_list(request):
    return HttpResponse(f"Hi, {request.user.username}")

