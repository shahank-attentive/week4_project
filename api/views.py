from django.shortcuts import render
from .models import User, Event
from .serializers import UserSerializer, EventSerializer
from rest_framework import viewsets, status, filters
from django.db.models import Model
from django.http import JsonResponse
from rest_framework.response import Response
from django.db.models import Q
from datetime import datetime
from django.utils import timezone
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class UserModelViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        query = dict(request.data)
        print(dict(request.data))
        Is_staff = query.get("is_staff")[0]
        print(Is_staff)
        if Is_staff == "True":
            if self.request.user.is_staff == True:
                print("admin me ho")
                if serializer.is_valid():
                    print("andar ho yr")
                    self.perform_create(serializer)
                    return Response(status=status.HTTP_201_CREATED)
            else:
                print("admin se bahar ho")
                return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        elif serializer.is_valid():
            self.perform_create(serializer)
            return Response(status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class EventModelViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # print(self.request.)
        serializer.save(organiser=self.request.user)

    def get_queryset(self):
        user = self.request.user.id
        filter_type = self.request.query_params.get("filter_type", None)
        myevents = self.request.query_params.get("myevents", None)
        print("filtertype", (type(myevents)))
        query_set = None
        if user == None:
            query_set = Event.objects.filter(
                Q(event_type="public") & Q(event_time_from__gte=timezone.now())
            )
            return query_set.distinct()
        else:
            # for staff
            Is_staff = self.request.user.is_staff
            if Is_staff:
                query_set = Event.objects.all()
                if filter_type == "future":
                    query_set = Event.objects.filter(
                        event_time_from__gte=timezone.now()
                    )
                if filter_type == "past":
                    query_set = Event.objects.filter(
                        event_time_till__lte=timezone.now()
                    )
                if filter_type == "ongoing":
                    query_set = Event.objects.filter(
                        event_time_from__lte=timezone.now(),
                        event_time_till__gte=timezone.now(),
                    )
                if filter_type == "public":
                    query_set = Event.objects.filter(event_type="public")

                return query_set.distinct()
            # for non-staff
            if filter_type == None and myevents == None:
                query_set = Event.objects.filter(
                    Q(organiser=user) | Q(event_type="public") | Q(users_invited=user)
                )
                return query_set.distinct()
            else:
                query_set2 = None
                if myevents == "True":
                    query_set2 = Event.objects.filter(organiser=user)

                if filter_type == "future":
                    query_set = Event.objects.filter(
                        (
                            Q(organiser=user)
                            | Q(event_type="public")
                            | Q(users_invited=user)
                        )
                        & Q(event_time_from__gte=timezone.now())
                    )
                elif filter_type == "ongoing":
                    query_set = Event.objects.filter(
                        (
                            Q(organiser=user)
                            | Q(event_type="public")
                            | Q(users_invited=user)
                        )
                        & Q(
                            event_time_from__lte=timezone.now(),
                            event_time_till__gte=timezone.now(),
                        )
                    )
                elif filter_type == "invited":
                    query_set = Event.objects.filter(
                        users_invited=user, event_time_till__gte=timezone.now()
                    )
                elif filter_type == "past":
                    query_set = Event.objects.filter(
                        (
                            Q(organiser=user)
                            | Q(users_invited=user)
                            | Q(event_type="public")
                        )
                        & Q(event_time_till__lte=timezone.now())
                    )
                if query_set2 is not None and query_set is not None:
                    return query_set.distinct() & query_set2.distinct()
                if query_set is not None:
                    return query_set.distinct()
                if query_set2 is not None:
                    return query_set2.distinct()

    def list(self, request):
        query_set = self.get_queryset()
        data = EventSerializer(query_set, many=True, context={"request": request})
        return Response(data.data)

    def update(self, request, pk=None, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(
            instance=instance,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        user = self.request.user.id
        Is_staff = self.request.user.is_staff
        print(Is_staff)
        if user == instance.organiser.id or Is_staff:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response({"msg": "error"})
        else:
            return Response({"msg": "user not allowed"})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        Is_staff = self.request.user.is_staff
        user = self.request.user.id
        # print(instance.organiser.id)
        if Is_staff or (
            int(user) == instance.organiser.id
            and instance.event_time_from > timezone.now()
        ):
            self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
