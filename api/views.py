from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser,FormParser
from .serializers import ResumeSerializer

class ResumeUploadView(APIView):
    parser_classes = [MultiPartParser,FormParser]

    def post(self,request,*args,**kwargs):
        serilaizer = ResumeSerializer(data=request.data)
        if serilaizer.is_valid():
            resume = serilaizer.save()
            resume.status = 'pending'
            resume.save()

            return Response({'resume_id':resume.id},status=status.HTTP_200_OK)
        return Response(serilaizer.errors,status=status.HTTP_400_BAD_REQUEST)
