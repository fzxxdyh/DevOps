from django import template
from django.utils.safestring import mark_safe
import time
import os

register = template.Library()

@register.simple_tag
def tag1(history_query_sets):
    return "tag test 123"

@register.simple_tag
def build_paginators(history_query_sets):
    return "teg test 456"


