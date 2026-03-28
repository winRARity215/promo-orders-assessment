from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import OrderCreateRequestSerializer, OrderSerializer
from ..services import OrderService
from django.core.exceptions import ValidationError as DjangoValidationError


class OrderCreateAPIView(APIView):
    
    def post(self, request: Request) -> Response:
        serializer = OrderCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            order = OrderService.create_order(
                user_id=data["user_id"],
                goods=data["goods"],
                promo_code=data.get("promo_code"),
            )
            order_data = OrderService.get_order_data(order)
            return Response(order_data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as exc:
            payload = {"error": str(exc)}
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    
    serializer_class = OrderSerializer
    lookup_field = "id"
    
    def get_queryset(self):
        from ..models import Order
        return Order.objects.select_related(
            "user", 
            "promo_code"
        ).prefetch_related("items__good")
    
    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        order = self.get_object()
        order_data = OrderService.get_order_data(order)
        return Response(order_data)
    
    @action(detail=False, methods=["get"])
    def by_user(self, request: Request) -> Response:
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {"error": "user_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        orders = self.get_queryset().filter(user_id=user_id)
        page = self.paginate_queryset(orders)
        if page is not None:
            return self.get_paginated_response(page)
        
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


from rest_framework.decorators import api_view

@api_view(["POST"])
def create_order_api(request: Request) -> Response:
    view = OrderCreateAPIView()
    return view.post(request)
