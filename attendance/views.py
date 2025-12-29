import base64
import io
import json
from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.core.files.base import ContentFile
from .forms import EmployeeSignUpForm, LoginForm
from .models import EmployeeProfile, Attendance

# try/import face_recognition but fail gracefully if not installed
try:
    import face_recognition
    import numpy as np
except Exception as exc:
    face_recognition = None

def home_view(request):
    return redirect('login')

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError

def register_view(request):
    # CASE 1: Logged-in user → complete profile only
    if request.user.is_authenticated:
        user = request.user

        if request.method == 'POST':
            employee_id = request.POST.get('employee_id')
            department = request.POST.get('department')
            face_image_data = request.POST.get('face_image_data')

            profile, created = EmployeeProfile.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': employee_id,
                    'department': department
                }
            )

            if not created:
                profile.employee_id = employee_id
                profile.department = department

            if face_image_data:
                header, encoded = face_image_data.split(',', 1)
                image_data = base64.b64decode(encoded)
                file_name = f'face_{employee_id}.png'
                profile.face_image.save(file_name, ContentFile(image_data), save=True)

                if face_recognition:
                    image = face_recognition.load_image_file(profile.face_image.path)
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        profile.face_encoding = json.dumps(encodings[0].tolist())

            profile.save()
            return redirect('dashboard')

        return render(request, 'register.html', {'profile_only': True})

    # CASE 2: New user signup
    if request.method == 'POST':
        form = EmployeeSignUpForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data.get('email', '')
                )
            except IntegrityError:
                return render(request, 'register.html', {
                    'form': form,
                    'error': 'Username already exists. Please login.'
                })

            EmployeeProfile.objects.create(
                user=user,
                employee_id=form.cleaned_data['employee_id'],
                department=form.cleaned_data.get('department', '')
            )

            login(request, user)
            return redirect('dashboard')

    else:
        form = EmployeeSignUpForm()

    return render(request, 'register.html', {'form': form})

def register_face_view(request):
    # simplified separate endpoint to register only face for existing user
    if request.method == 'POST':
        username = request.POST.get('username')
        face_data = request.POST.get('face_data')
        try:
            user = User.objects.get(username=username)
            profile = EmployeeProfile.objects.get(user=user)
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
        header, encoded = face_data.split(',', 1)
        image_data = base64.b64decode(encoded)
        file_name = f'face_{profile.employee_id}.png'
        profile.face_image.save(file_name, ContentFile(image_data), save=True)

        if face_recognition:
            image = face_recognition.load_image_file(profile.face_image.path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                profile.face_encoding = json.dumps(encodings[0].tolist())
                profile.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                return render(request, 'login.html', {'form': form, 'error': 'Invalid credentials'})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        profile = EmployeeProfile.objects.get(user=request.user)
    except EmployeeProfile.DoesNotExist:
        return redirect('register')

    attendance_entries = []

    if profile:
        today = date.today()
        number_of_days = 7   # you can change this to 30 if needed

        # Generate last N dates (including today)
        recent_dates = [today - timedelta(days=day) for day in range(number_of_days)]

        # Fetch existing attendance records for the employee
        existing_records = Attendance.objects.filter(
            employee=profile,
            date__in=recent_dates
        )

        # Map records by date for fast lookup
        attendance_by_date = {
            record.date: record for record in existing_records
        }

        # Build final attendance list (Present + Absent)
        for current_date in recent_dates:
            if current_date in attendance_by_date:
                record = attendance_by_date[current_date]
                attendance_entries.append({
                    'date': current_date,
                    'check_in_time': record.check_in_time,
                    'status': 'Present'
                })
            else:
                attendance_entries.append({
                    'date': current_date,
                    'check_in_time': None,
                    'status': 'Absent'
                })

    return render(request, 'dashboard.html', {
        'profile': profile,
        'attendance_entries': attendance_entries
    })


@csrf_exempt
def recognize_view(request):
    'API endpoint to accept webcam capture and mark attendance if face matches'
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)
    if not face_recognition:
        return JsonResponse({'status': 'error', 'message': 'face_recognition library not installed'}, status=500)

    data = json.loads(request.body.decode('utf-8'))
    image_data = data.get('image')
    if not image_data:
        return JsonResponse({'status': 'error', 'message': 'No image provided'}, status=400)
    header, encoded = image_data.split(',', 1)
    image_bytes = base64.b64decode(encoded)
    image_stream = io.BytesIO(image_bytes)
    image = face_recognition.load_image_file(image_stream)
    faces_encodings = face_recognition.face_encodings(image)
    if not faces_encodings:
        return JsonResponse({'status': 'error', 'message': 'No face detected'}, status=400)

    found_encoding = faces_encodings[0]
    # gather all stored employee encodings
    all_profiles = EmployeeProfile.objects.exclude(face_encoding__isnull=True).exclude(face_encoding__exact='')
    known_encodings = []
    known_employee_ids = []
    for profile in all_profiles:
        try:
            encoding_list = json.loads(profile.face_encoding)
            known_encodings.append(encoding_list)
            known_employee_ids.append(profile.employee_id)
        except Exception:
            continue

    import numpy as np
    matches = face_recognition.compare_faces([np.array(e) for e in known_encodings], np.array(found_encoding), tolerance=0.5)
    if True in matches:
        matched_index = matches.index(True)
        matched_employee_id = known_employee_ids[matched_index]
        try:
            matched_profile = EmployeeProfile.objects.get(employee_id=matched_employee_id)
        except EmployeeProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Matched profile not found'}, status=500)

        today = date.today()
        now_time = datetime.now().time()
        attendance_record, created = Attendance.objects.get_or_create(employee=matched_profile, date=today,
                                                                      defaults={'check_in_time': now_time, 'status': 'Present'})
        if not created:
            # already exists, update check_in_time only if empty
            if not attendance_record.check_in_time:
                attendance_record.check_in_time = now_time
                attendance_record.save()
        return JsonResponse({'status': 'ok', 'employee': matched_profile.employee_id, 'first_name': matched_profile.user.first_name})
    else:
        return JsonResponse({'status': 'error', 'message': 'No match found'}, status=404)

def attendance_list_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    today = date.today()
    number_of_days = 7
    recent_dates = [today - timedelta(days=i) for i in range(number_of_days)]

    attendance_entries = []

    # ADMIN VIEW → all employees
    if request.user.is_staff:
        employees = EmployeeProfile.objects.all()

    # EMPLOYEE VIEW → only own records
    else:
        try:
            employees = [EmployeeProfile.objects.get(user=request.user)]
        except EmployeeProfile.DoesNotExist:
            employees = []

    for employee in employees:
        records = Attendance.objects.filter(
            employee=employee,
            date__in=recent_dates
        )

        record_map = {record.date: record for record in records}

        for current_date in recent_dates:
            if current_date in record_map:
                attendance_entries.append({
                    'employee': employee,
                    'date': current_date,
                    'check_in_time': record_map[current_date].check_in_time,
                    'status': 'Present'
                })
            else:
                attendance_entries.append({
                    'employee': employee,
                    'date': current_date,
                    'check_in_time': None,
                    'status': 'Absent'
                })

    return render(request, 'attendance_list.html', {
        'entries': attendance_entries
    })

