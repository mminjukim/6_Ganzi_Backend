from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from collections import defaultdict
from datetime import date

from accounts.models import User
from sch_requests.models import Request, FamilyInfo, FamilySchedule
from .serializers import *

# Create your views here.


# 메인 > 스케줄 전부 확인하기 (가족 캘린더)
class FamilyCalendarView(APIView):
    def get(self, request, y, m, d):
        user = request.user
        user_family = FamilyInfo.objects.get(family_id=user.family.family_id)
        family_members = User.objects.filter(family=user_family)
 
        schedules = defaultdict(lambda: {"fam_schedule_id": "", "category_name": "", "schedule_title": "", 
                                         "schedule_start_time": "", "schedule_end_time": "", 
                                         "schedule_memo": "", "target_users": []})
        for member in family_members:
            requests = Request.objects.filter(target_user=member, is_accepted=True)
            member_img = ProfileImgSerializer(user, context={'request': request}).data['profile_img']

            for req in requests:
                fam_schedule = req.fam_schedule

                if fam_schedule.schedule_start_time.date() == date(y, m, d):
                    if fam_schedule.fam_schedule_id not in schedules:
                        schedules[fam_schedule.fam_schedule_id]["category_name"] = fam_schedule.category.category_name
                        schedules[fam_schedule.fam_schedule_id]["schedule_title"] = fam_schedule.schedule_title
                        schedules[fam_schedule.fam_schedule_id]["schedule_start_time"] = fam_schedule.schedule_start_time.strftime("%H:%M")
                        schedules[fam_schedule.fam_schedule_id]["schedule_end_time"] = fam_schedule.schedule_end_time.strftime("%H:%M")
                        schedules[fam_schedule.fam_schedule_id]["schedule_memo"] = fam_schedule.schedule_memo
                    
                    schedules[fam_schedule.fam_schedule_id]["target_users"].append(member_img)

        result = [{"category_name": v["category_name"], "schedule_title": v["schedule_title"], 
                   "schedule_start_time": v["schedule_start_time"], "schedule_end_time": v["schedule_end_time"],
                   "schedule_memo": v["schedule_memo"], "target_users": v["target_users"]}
                  for v in schedules.values()]

        return Response(result, status=status.HTTP_200_OK)


# 받은 스케줄 목록 view
class AllIncomingRequestsView(APIView):
    def get(self, request):
        requests = Request.objects.filter(target_user=request.user, 
                                          is_accepted=False, is_checked=False).order_by('-id')[:100]
        req_data = []
        i = 0
        while i < requests.count():
            req_id = requests[i].id
            schedule = requests[i].fam_schedule
            if schedule.is_daily:
                req_id -= 6
            elif schedule.is_weekly:
                req_id -= 3
            elif schedule.is_monthly:
                req_id -= 11
            elif schedule.is_yearly:
                req_id -= 4
            req = Request.objects.get(id=req_id)
            req_data.append(RequestListSerializer(req, context={'request': request}).data)
            i += (requests[i].id - req_id) + 1
            if i == requests.count(): break
        return Response(req_data, status=status.HTTP_200_OK)
            
    
# 받은 스케줄 상세 view
class IncomingRequestView(APIView):
    def get(self, request, id):
        incoming_request = Request.objects.get(id=id)
        request_data = RequestSerializer(incoming_request).data
        return Response(request_data, status=status.HTTP_200_OK)
    
    def post(self, request, id): # 받은 스케줄 수락
        incoming_request = Request.objects.get(id=id)
        schedule = FamilySchedule.objects.get(fam_schedule_id=incoming_request.fam_schedule.fam_schedule_id)
        i = id
        repeat_cnt = id+1
        if schedule.is_daily:
            repeat_cnt = id+7
        elif schedule.is_weekly:
            repeat_cnt = id+4
        elif schedule.is_monthly:
            repeat_cnt = id+12
        elif schedule.is_yearly:
            repeat_cnt = id+5
        while i < repeat_cnt:
            req = Request.objects.get(id=i)
            req.is_checked = True
            req.is_accepted = True
            req.save(update_fields=['is_checked', 'is_accepted'])
            i += 1
            if i == repeat_cnt: break
        return Response({'message':'스케줄이 확정되었습니다'}, status=status.HTTP_200_OK)

    def delete(self, request, id): # 받은 스케줄 거절
        incoming_request = Request.objects.get(id=id)
        schedule = FamilySchedule.objects.get(fam_schedule_id=incoming_request.fam_schedule.fam_schedule_id)
        i = id
        repeat_cnt = id+1
        if schedule.is_daily:
            repeat_cnt = id+7
        elif schedule.is_weekly:
            repeat_cnt = id+4
        elif schedule.is_monthly:
            repeat_cnt = id+12
        elif schedule.is_yearly:
            repeat_cnt = id+5
        while i < repeat_cnt:
            req = Request.objects.get(id=i)
            req.is_checked = True
            req.is_accepted = False
            req.save(update_fields=['is_checked', 'is_accepted'])
            i += 1
            if i == repeat_cnt: break
        return Response({'message':'거절한 스케줄로 이동되었습니다'}, status=status.HTTP_200_OK)


# 거절 스케줄 목록 view
class AllDeclinedRequestsView(APIView):
    def get(self, request):
        requests = Request.objects.filter(target_user=request.user, 
                                          is_accepted=False, is_checked=True).order_by('-id')[:100]
        req_data = []
        i = 0
        while i < requests.count():
            req_id = requests[i].id
            schedule = requests[i].fam_schedule
            if schedule.is_daily:
                req_id -= 6
            elif schedule.is_weekly:
                req_id -= 3
            elif schedule.is_monthly:
                req_id -= 11
            elif schedule.is_yearly:
                req_id -= 4
            req = Request.objects.get(id=req_id)
            req_data.append(RequestListSerializer(req, context={'request': request}).data)
            i += (requests[i].id - req_id) + 1
            if i == requests.count(): break
        return Response(req_data, status=status.HTTP_200_OK)
    
# 거절 스케줄 상세 view
class DeclinedRequestView(APIView):
    def get(self, request, id):
        declined_request = Request.objects.get(id=id)
        request_data = RequestSerializer(declined_request).data
        return Response(request_data, status=status.HTTP_200_OK)
    
    def post(self, request, id): # 거절 스케줄 다시 수락
        declined_request = Request.objects.get(id=id)
        schedule = FamilySchedule.objects.get(fam_schedule_id=declined_request.fam_schedule.fam_schedule_id)
        i = id
        repeat_cnt = id+1
        if schedule.is_daily:
            repeat_cnt = id+7
        elif schedule.is_weekly:
            repeat_cnt = id+4
        elif schedule.is_monthly:
            repeat_cnt = id+12
        elif schedule.is_yearly:
            repeat_cnt = id+5
        while i < repeat_cnt:
            req = Request.objects.get(id=i)
            req.is_accepted = True
            req.save(update_fields=['is_accepted'])
            i += 1
            if i == repeat_cnt: break
        return Response({'message':'스케줄이 확정되었습니다'}, status=status.HTTP_200_OK)

    def delete(self, request, id): # 거절 스케줄 삭제 
        declined_request = Request.objects.get(id=id)
        schedule = FamilySchedule.objects.get(fam_schedule_id=declined_request.fam_schedule.fam_schedule_id)
        i = id
        repeat_cnt = id+1
        if schedule.is_daily:
            repeat_cnt = id+7
        elif schedule.is_weekly:
            repeat_cnt = id+4
        elif schedule.is_monthly:
            repeat_cnt = id+12
        elif schedule.is_yearly:
            repeat_cnt = id+5
        while i < repeat_cnt:
            req = Request.objects.get(id=i)
            schedule = FamilySchedule.objects.get(fam_schedule_id=req.fam_schedule.fam_schedule_id)
            req.delete()
            schedule.delete()
            i += 1
            if i == repeat_cnt: break
        return Response({"message":"스케줄이 삭제되었습니다"}, status=status.HTTP_204_NO_CONTENT)


# 보낸 스케줄 목록 view
class AllOutgoingRequestsView(APIView):
    def get(self, request):
        requests = Request.objects.filter(sent_user=request.user).order_by('-id')[:300]
        req_data = []
        i = 0
        while i < requests.count():
            req_id = requests[i].id
            schedule = requests[i].fam_schedule
            targets_cnt = Request.objects.filter(fam_schedule=requests[i].fam_schedule).count()
            if schedule.is_daily:
                req_id -= (7 * targets_cnt - 1)
            elif schedule.is_weekly:
                req_id -= (4 * targets_cnt - 1)
            elif schedule.is_monthly:
                req_id -= (12 * targets_cnt - 1)
            elif schedule.is_yearly:
                req_id -= (5 * targets_cnt - 1)
            else: 
                req_id -= (targets_cnt - 1)
            req = Request.objects.get(id=req_id)
            req_data.append(RequestListSerializer(req, context={'request': request}).data)
            i += (requests[i].id - req_id) + 1
            if i == requests.count(): break
        return Response(req_data, status=status.HTTP_200_OK)
    
# 보낸 스케줄 상세 view
class OutgoingRequestView(APIView):
    def get(self, request, id):
        sent_request = Request.objects.get(id=id)
        request_data = RequestSerializer(sent_request).data
        return Response(request_data, status=status.HTTP_200_OK)
    
    def delete(self, request, id): # 보낸 스케줄 요청 취소 
        sent_request = Request.objects.get(id=id)
        schedule = FamilySchedule.objects.get(fam_schedule_id=sent_request.fam_schedule.fam_schedule_id)
        targets_cnt = Request.objects.filter(fam_schedule=schedule).count()
        i = id
        if schedule.is_daily:
            repeat_cnt = (7 * targets_cnt)
        elif schedule.is_weekly:
            repeat_cnt = (4 * targets_cnt)
        elif schedule.is_monthly:
            repeat_cnt = (12 * targets_cnt)
        elif schedule.is_yearly:
            repeat_cnt = (5 * targets_cnt)
        else: 
            repeat_cnt = 1
        while i < id+repeat_cnt:
            req = Request.objects.get(id=i)
            schedule = FamilySchedule.objects.get(fam_schedule_id=req.fam_schedule.fam_schedule_id)
            req.delete()
            schedule.delete()
            i += 1
            if i == id+repeat_cnt: break
        return Response({"message":"요청이 취소되었습니다"}, status=status.HTTP_204_NO_CONTENT)