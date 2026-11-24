from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

DEFAULT_FILTER_BACKENDS = [
    DjangoFilterBackend,
    SearchFilter, 
    OrderingFilter
]