from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render, redirect
from exemptions.models import Exemption, Teacher
from exemptions.models import StringsList, CourseList
from django.contrib import messages


# Create your views here.
def home(request):
    if request.method == "POST":
        student_id = int(request.POST["id"])
        student_model = Exemption.objects.get_or_create(identifier=student_id)[0]
        return render(request, "table.html", {"courses": [course for course in student_model.exempted_strings.all()], "model": student_model})

    return render(request,  "base.html")


def teacher(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("teacher_list")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")


def teacher_list(request):
    teacher_model = Teacher.objects.get_or_create(identifier=request.user.username)[0]
    curr_courses = sorted(teacher_model.classes.all(), key=lambda c: c.period)

    if request.method == "GET":
        return render(request, "teacher_home.html", {"username": request.user.username,
                                                     "courses": None if curr_courses is None else curr_courses})

    if request.POST.get("courseName"):
        course = CourseList.objects.create(name=request.POST["courseName"], period=int(request.POST.get("select")))
        teacher_model.classes.add(course)
        return redirect("teacher_list")

    if request.POST.get("studentID"):
        student_model = Exemption.objects.get_or_create(identifier=int(request.POST["studentID"]))[0]
        course_string = request.POST["exempt-class"]
        course = CourseList.objects.get_or_create(name=course_string[:course_string.find("-")], period=int(course_string[-1]))
        student_model.exempted_strings.add(course[0])
        student_model.exemptions_used.__add__(1)

        teacher_model.exempted_ids.add(request.POST["studentID"])

        return redirect("teacher_list")

    for course in curr_courses:
        if request.POST.get(course.name) == "on":
            teacher_model.classes.remove(course)

    return redirect("teacher_list")