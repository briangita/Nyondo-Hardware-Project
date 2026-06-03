from django import template

register = template.Library()

@register.filter
def has_role(user, role):
    return user.is_superuser or user.groups.filter(name=role).exists()