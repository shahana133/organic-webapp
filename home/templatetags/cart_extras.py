# home/templatetags/cart_extras.py
from django import template

register = template.Library()

@register.filter
def to_range(start, end):
    return range(start, end)
