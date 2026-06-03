from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps


def role_required(allowed_roles):
    """
    Generic role-based decorator.

    Usage:
        @role_required(['admin'])
        @role_required(['admin', 'accounts'])
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # Check authentication
            if not request.user.is_authenticated:
                messages.error(request, "Please login to continue.")
                return redirect('login')

            # Superuser bypass
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Get user roles
            user_groups = list(request.user.groups.values_list('name', flat=True))

            # Check role access
            if not any(role in user_groups for role in allowed_roles):
                messages.error(request, "You do not have permission to access this page.")
                return redirect('login')

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator

def admin_required(view_func):
    return role_required(['admin'])(view_func)


def accounts_required(view_func):
    return role_required(['accounts'])(view_func)


def sales_attendant_required(view_func):
    return role_required(['sales_attendant'])(view_func)


def store_manager_required(view_func):
    return role_required(['store_manager'])(view_func)


def admin_or_accounts_required(view_func):
    return role_required(['admin', 'accounts'])(view_func)

def admin_or_sales_attendant_required(view_func):
    return role_required(['admin', 'sales_attendant'])(view_func)

def admin_or_store_manager_required(view_func):
    return role_required(['admin', 'store_manager'])(view_func)

def admin_or_accounts_or_store_manager_required(view_func):
    return role_required(['admin', 'accounts', 'store_manager'])(view_func)

def admin_or_accounts_or_sales_attendant_required(view_func):
    return role_required(['admin', 'accounts', 'sales_attendant'])(view_func)