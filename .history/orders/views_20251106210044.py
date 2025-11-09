from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderSerializer

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def user_orders(self, request):
        if request.user.is_staff and 'user_id' in request.GET:
            orders = Order.objects.filter(user_id=request.GET['user_id'])
        else:
            orders = self.get_queryset()
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)