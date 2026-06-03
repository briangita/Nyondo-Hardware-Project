from django.shortcuts import render, redirect , get_object_or_404
from django.contrib.auth.models import Group
from django.contrib import messages
from .forms import UserRegisterForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages
from users.decorators import admin_required, accounts_required, admin_or_accounts_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

# Create your views here.

def register(request):

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Admin must approve
            user.save()

            role = form.cleaned_data.get('role')

            try:
                group = Group.objects.get(name=role)
                user.groups.add(group)
            except Group.DoesNotExist:
                messages.error(request, "Selected role is not configured.")
                return redirect('register')

            messages.success(
                request,
                'Account created successfully. Await admin approval.'
            )

            return redirect('login')

    else:
        form = UserRegisterForm()

    return render(request, 'registration/register.html', {
        'form': form
    })

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        user = self.request.user

        if not user.is_active:
            return reverse_lazy('login')

        groups = user.groups.values_list('name', flat=True) # Get group names as a list

        if user.is_superuser or 'admin' in groups:
            return reverse_lazy('manager_dashboard')

        if 'accounts' in groups:
            return reverse_lazy('reports_home')

        if 'store_manager' in groups:
            return reverse_lazy('stock_dashboard')

        if 'sales_attendant' in groups:
            return reverse_lazy('sales_dashboard')

        return reverse_lazy('login')

User = get_user_model()


#  View: List Pending Users
@login_required
@admin_required
def approve_users(request):
    pending_users = User.objects.filter(
        is_active=False
    ).order_by('-date_joined')

    return render(request, 'approve_users.html', {
        'pending_users': pending_users
    })


#  View: Approve User

@login_required
@admin_required
def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.is_active = True
        user.save()

        messages.success(
            request,
            f"{user.username} approved successfully."
        )

    return redirect('approve_users')


#  View: Reject (Delete) User

@login_required
@admin_required
def reject_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        username = user.username
        user.delete()

        messages.warning(
            request,
            f"{username} has been rejected and removed."
        )

    return redirect('approve_users')

@login_required
@admin_required
def manage_users(request):

    users = User.objects.all().order_by('-date_joined')

    return render(request, 'manage_users.html', {
        'users': users
    })

@login_required
@admin_required
def toggle_user_status(request, user_id):

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.is_active = not user.is_active
        user.save()

        status = "activated" if user.is_active else "deactivated"

        messages.success(request, f"{user.username} has been {status}.")

    return redirect('manage_users')