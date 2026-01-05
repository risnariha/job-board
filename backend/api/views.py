from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import User, Job, JobCategory, JobApplication, SavedJob
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, 
    UserProfileSerializer, JobSerializer, JobCategorySerializer,
    JobApplicationSerializer, SavedJobSerializer
)
from .permissions import IsOwnerOrReadOnly, IsEmployer, IsJobSeeker

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserProfileSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserProfileSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['job_type', 'experience_level', 'category', 'location']
    search_fields = ['title', 'description', 'company__company_name']
    ordering_fields = ['created_at', 'salary_min', 'salary_max']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsEmployer]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsJobSeeker])
    def apply(self, request, pk=None):
        job = self.get_object()
        
        # Check if user already applied
        if JobApplication.objects.filter(job=job, applicant=request.user).exists():
            return Response(
                {'detail': 'You have already applied for this job.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if job is expired
        if job.is_expired:
            return Response(
                {'detail': 'This job posting has expired.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = JobApplicationSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(job=job)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def save(self, request, pk=None):
        job = self.get_object()
        saved_job, created = SavedJob.objects.get_or_create(job=job, user=request.user)
        
        if created:
            serializer = SavedJobSerializer(saved_job)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            saved_job.delete()
            return Response({'detail': 'Job removed from saved list.'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def saved(self, request):
        saved_jobs = SavedJob.objects.filter(user=request.user).order_by('-saved_at')
        serializer = SavedJobSerializer(saved_jobs, many=True)
        return Response(serializer.data)

class JobApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'employer':
            # Employers see applications for their jobs
            return JobApplication.objects.filter(job__company=user)
        else:
            # Job seekers see their own applications
            return JobApplication.objects.filter(applicant=user)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        if 'status' in serializer.validated_data:
            instance.reviewed_at = timezone.now()
            instance.save()

class JobCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    permission_classes = [permissions.AllowAny]