from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.conf import settings
from urllib.parse import urlsplit, urlunsplit

from core.logging_context import get_request_id


class CustomPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 1000

    def _with_base_url(self, link):
        if not link:
            return link

        base_url = getattr(settings, "BASE_URL", "")
        if not base_url:
            return link

        base_parts = urlsplit(base_url)
        if not base_parts.scheme or not base_parts.netloc:
            return link

        link_parts = urlsplit(link)
        return urlunsplit(
            (
                base_parts.scheme,
                base_parts.netloc,
                link_parts.path,
                link_parts.query,
                link_parts.fragment,
            )
        )

    def get_paginated_response(self, data):
        next_link = self._with_base_url(self.get_next_link())
        previous_link = self._with_base_url(self.get_previous_link())

        return Response(
            {
                "success": True,
                "message": "Data fetched successfully!",
                "request_id": get_request_id(),
                "meta": {
                    "total_items": self.page.paginator.count,
                    "total_pages": self.page.paginator.num_pages,
                    "current_page": self.page.number,
                    "next": next_link,
                    "previous": previous_link,
                    "per_page": self.page_size,
                },
                "data": data,
            }
        )
