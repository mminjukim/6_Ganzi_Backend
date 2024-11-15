from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from sch_requests.models import Request
from .serializers import *

# Create your views here.

# 받은 스케줄 목록 view
class AllIncomingRequestsView(APIView):
    def get(self, request):
        requests = Request.objects.filter(target_user_id=request.user, 
                                          is_accepted=False, is_checked=False)
        requests_data = RequestListSerializer(requests, many=True).data
        return Response(requests_data, status=status.HTTP_200_OK)
    
# 받은 스케줄 상세 view
class IncomingRequestView(APIView):
    def get(self, request, id):
        incoming_request = Request.objects.get(id=id)
        request_data = RequestSerializer(incoming_request).data
        return Response(request_data, status=status.HTTP_200_OK)
    
    def post(self, request, id): # 받은 스케줄 수락
        incoming_request = Request.objects.get(id=id)
        incoming_request.is_checked = True
        incoming_request.is_accepted = True
        incoming_request.save(update_fields=['is_checked', 'is_accepted'])
        return Response({'message':'스케줄이 확정되었습니다'}, status=status.HTTP_200_OK)

    def delete(self, request, id): # 받은 스케줄 거절
        incoming_request = Request.objects.get(id=id)
        incoming_request.is_checked = True
        incoming_request.is_accepted = True
        incoming_request.save(update_fields=['is_checked', 'is_accepted'])
        return Response({'message':'거절한 스케줄로 이동되었습니다'}, status=status.HTTP_200_OK)

