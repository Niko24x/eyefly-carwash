from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, login
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from appointments.models import Appointment, AppointmentStatus

from .forms import ProfileEditForm, RegisterForm, StaffUserCreationForm, UserForm
from .models import UserProfile


User = get_user_model()


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Tu cuenta fue creada correctamente.')
            return redirect('appointment_list')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def account_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    active_appointments = Appointment.objects.filter(
        user=request.user,
        status=AppointmentStatus.ACTIVE,
    ).count()
    total_appointments = Appointment.objects.filter(user=request.user).count()

    return render(
        request,
        'accounts/account_profile.html',
        {
            'profile': profile,
            'vehicles': request.user.vehicles.all(),
            'active_appointments': active_appointments,
            'total_appointments': total_appointments,
        },
    )


@login_required
def account_profile_edit(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, user=request.user, profile=profile)
        if form.is_valid():
            form.save(request.user, profile)
            messages.success(request, 'Tu perfil fue actualizado correctamente.')
            return redirect('account_profile')
    else:
        form = ProfileEditForm(user=request.user, profile=profile)

    return render(
        request,
        'accounts/account_profile_edit.html',
        {
            'form': form,
        },
    )


@staff_member_required
def user_list(request):
    users = User.objects.annotate(appointment_count=Count('appointments')).order_by(
        '-date_joined'
    )
    return render(request, 'accounts/user_list.html', {'users': users})


@staff_member_required
def user_create(request):
    if request.method == 'POST':
        form = StaffUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'El usuario fue registrado correctamente.')
            return redirect('user_list')
    else:
        form = StaffUserCreationForm()

    return render(
        request,
        'accounts/user_form.html',
        {
            'form': form,
            'page_title': 'Registrar usuario',
            'page_description': 'Crea una cuenta para un cliente o administrador.',
            'submit_label': 'Guardar usuario',
        },
    )


@staff_member_required
def user_update(request, pk):
    account = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, 'El usuario fue actualizado correctamente.')
            return redirect('user_list')
    else:
        form = UserForm(instance=account)

    return render(
        request,
        'accounts/user_form.html',
        {
            'form': form,
            'account': account,
            'page_title': 'Editar usuario',
            'page_description': 'Actualiza los datos del usuario seleccionado.',
            'submit_label': 'Guardar cambios',
        },
    )
