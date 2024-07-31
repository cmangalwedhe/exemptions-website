from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect

import csv

from exemptions.forms import CSVUploadForm
from exemptions.models import Exemption, Teacher
from exemptions.models import StringsList, CourseList
from django.contrib import messages
from django.db.models import F


# Create your views here.
def home(request):
    if request.method == "POST":
        student_id = int(request.POST["id"])
        student_model = Exemption.objects.get_or_create(identifier=student_id)[0]
        return render(request, "table.html",
                      {"courses": [course for course in student_model.exempted_strings.all()], "model": student_model})

    return render(request, "base.html")


def teacher(request):
    if request.method == "GET" and request.user.is_authenticated:
        return redirect("teacher_list")

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("teacher_list")
        else:
            messages.error(request, "Invalid username or password")
            return redirect("teachers")

    return render(request, "login.html")


@login_required(login_url="/teachers")
def teacher_list(request):
    teacher_model = Teacher.objects.get_or_create(identifier=request.user.username)[0]
    curr_courses = sorted(teacher_model.classes.all(), key=lambda c: c.period)

    if request.method == "GET":
        return render(request, "teacher_home.html", {"username": request.user.username,
                                                     "courses": None if curr_courses is None else curr_courses})

    if request.POST.get("courseName"):
        course = CourseList.objects.create(name=request.POST["courseName"], period=int(request.POST.get("select")))

        if teacher_model.classes.all().filter(name=course.name, period=course.period):
            messages.error(request, f"Course {course.name} - Period {course.period} already exists")
            return redirect("teacher_list")

        teacher_model.classes.add(course)
        teacher_model.save()
        messages.success(request, f"Course {course.name} - Period {course.period} has been added!")
        return redirect("teacher_list")

    if request.POST.get("studentID"):
        try:
            student_model = Exemption.objects.get(identifier=int(request.POST["studentID"]))[0]
        except Exemption.DoesNotExist:
            messages.error(request, "Student ID not registered with school database, please contact APs")
            return redirect("teacher_list")

        course_string = request.POST["exempt-class"]
        name = course_string[:course_string.find("-") - 1]
        period = int(course_string[-1])
        course = CourseList.objects.get_or_create(name=name, period=period)

        if student_model.exempted_strings.all().filter(name=name, period=period).exists():
            messages.error(request,
                           f"Student ID {request.POST['studentID']} is already exempted for {name} - Period {period}")
            return redirect("teacher_list")

        if student_model.exemptions_used == student_model.available_exemptions:
            error_message = "Student has reached their maximum number of exemptions<br>"
            error_message += "Student's current exemption list:<br>"

            for s in student_model.exempted_strings.all():
                error_message += f"   • {s.name} - Period {s.period}<br>"

            messages.error(request, error_message)

        student_model.exempted_strings.add(course[0])
        student_model.exemptions_used = F("exemptions_used") + 1
        student_model.save()

        exempted_id = StringsList.objects.get_or_create(value=request.POST["studentID"])[0]
        teacher_model.exempted_ids.add(exempted_id)
        teacher_model.save()
        messages.success(request,
                         f"Student ID {request.POST['studentID']} has been exempted for {name} - Period {period}")

        return redirect("teacher_list")

    if request.POST.get("studentID2"):
        teacher_model = Teacher.objects.get_or_create(identifier=request.user.username)[0]

        if not teacher_model.exempted_ids.all().contains(
                StringsList.objects.get_or_create(value=request.POST["studentID2"])[0]):
            messages.error(request, f"{request.POST['studentID2']} is not exempted for any of your classes")
        else:
            student_model = Exemption.objects.get_or_create(identifier=int(request.POST["studentID2"]))[0]
            courses_to_pick = [s.name.strip() for s in student_model.exempted_strings.all()]
            teacher_courses = [course.name for course in teacher_model.classes.all()]
            filtered = [c for c in courses_to_pick if teacher_courses.__contains__(c)]

            return render(request, "teacher_home.html", context={"unexempt": True,
                                                                 "unexempt_courses": filtered,
                                                                 "student_id": request.POST["studentID2"]})

        return redirect("teacher_list")

    if request.POST.get("studentID3"):
        student_model = Exemption.objects.get_or_create(identifier=int(request.POST["studentID3"]))[0]
        count = 0
        student_id = None

        for id in teacher_model.exempted_ids.all():
            if id.value == request.POST["studentID3"]:
                count += 1
                student_id = id

        if count == 1:
            teacher_model.exempted_ids.remove(student_id)
            teacher_model.save()

        for stu_courses in student_model.exempted_strings.all():
            if request.POST.get(stu_courses.name) == "on":
                student_model.exemptions_used = max(0, F("exemptions_used") - 1)
                student_model.exempted_strings.remove(stu_courses)
                student_model.save()
                messages.success(request,
                                 f"Student {request.POST['studentID3']} has been unexempted from {stu_courses.name} - Period {stu_courses.period}")

        return redirect("teacher_list")

    if request.POST.get("studentID4"):
        student_model = Exemption.objects.get_or_create(identifier=int(request.POST["studentID4"]))[0]
        courses_to_pick = [f"{s.name} - Period {s.period}" for s in student_model.exempted_strings.all()]
        teacher_courses = [f"{course.name} - Period {course.period}" for course in teacher_model.classes.all()]
        filtered = [c for c in courses_to_pick if teacher_courses.__contains__(c)]

        if len(filtered) == 0:
            messages.error(request, f"You have not Student {request.POST['studentID4']} from any of your classes")
        else:
            for s in filtered:
                messages.success(request, f"Student {request.POST['studentID4']} is exempted from {s}")

    teacher_classes = [f"{course.name} - {course.period}" for course in teacher_model.classes.all()]

    if request.POST.get("logout"):
        logout(request)
        messages.success(request, f"You have been successfully logged out!")
        return redirect("teachers")

    for key, value in request.POST.items():
        if value == "on" and teacher_classes.__contains__(key):
            for course in teacher_model.classes.all():
                if f"{course.name} - {course.period}" == key:
                    teacher_model.classes.remove(course)
                    teacher_model.save()
                    messages.success(request,
                                     f"{course.name} - Period {course.period} has been deleted from your class list!")
                    break

    return redirect("teacher_list")


def admin_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            print(user.groups.filter(name="administrators").exists())
            return redirect("administration")
        else:
            messages.error(request, "Invalid username or password: ")
            return redirect("admin_login")

    return render(request, "admin_login.html")


@login_required(login_url='/admin-login')
def administration(request):
    if request.method == "POST":
        if request.POST.get("studentID"):
            try:
                student_model = Exemption.objects.get(identifier=int(request.POST["studentID"]))
            except Exemption.DoesNotExist:
                student_model = None

            if student_model is None:
                messages.error(request, f"Student ID {request.POST["studentID"]} is not in the database")
                return redirect("administration")
            else:
                exemption_notice = f"Student ID {request.POST["studentID"]} has been exempted from the following courses:"

                if student_model.exemptions_used:
                    for course in student_model.exempted_strings.all():
                        exemption_notice += f"<br>• {course.name} - Period {course.period}"
                else:
                    exemption_notice += "<br>\t• Student is not exempted from any courses."

                exemption_notice += f"<br>Exemptions Used: {student_model.exemptions_used}"
                exemption_notice += f"<br>Available Exemptions: {student_model.available_exemptions}"
                messages.success(request, exemption_notice)
                return redirect("administration")

        elif 'file' in request.FILES:
            form = CSVUploadForm(request.POST, request.FILES)

            if form.is_valid():
                csv_file = request.FILES['file']

                if not csv_file.name.endswith('.csv'):
                    messages.error(request, "Uploaded file is not type csv")
                else:
                    file = csv_file.read().decode('utf-8').splitlines()
                    reader = csv.DictReader(file)

                    students_created = 0
                    spring_semester = request.POST.get("spring_semester") == "on"
                    exemptions = {'9': 1, '10': 2, '11': 3, '12': 7 if spring_semester else 4}

                    for row in reader:
                        student, created = Exemption.objects.get_or_create(
                            identifier=int(row['student id']),
                            defaults={
                                'available_exemptions': exemptions[row['grade level']],
                                'exemptions_used': 0
                            }
                        )

                        if created:
                            students_created += 1

                    messages.success(request, f"Successfully added {students_created} students into database")
                    return redirect("administration")
            else:
                messages.error(request, "Invalid submission")
                return redirect("administration")
        else:
            logout(request)
            messages.success(request, f"You have been successfully logged out!")
            return redirect("admin_login")


    else:
        upload_form = CSVUploadForm()
        return render(request, "admin_home.html", {"form": upload_form})