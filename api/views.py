from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser,FormParser
from .serializers import ResumeSerializer
from django.utils import timezone
from services.pipeline import process_resume

class ResumeUploadView(APIView):
    parser_classes = [MultiPartParser,FormParser]

    def post(self,request,*args,**kwargs):
        serializer = ResumeSerializer(data=request.data)
        if serializer.is_valid():
            resume = serializer.save()
            try:
                analyzed_response = process_resume(resume)
                for field, value in analyzed_response.items():
                    setattr(resume, field, value)
                resume.status = "completed"
                resume.error_message = None
                response_status = status.HTTP_200_OK
            except Exception as exc:
                resume.status = "failed"
                resume.error_message = str(exc)
                response_status = status.HTTP_422_UNPROCESSABLE_ENTITY
            resume.processed_at = timezone.now()
            resume.save()
            return Response({'resume_id':resume.id, 'status': resume.status},status=response_status)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
