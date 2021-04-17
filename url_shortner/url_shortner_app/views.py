from django.shortcuts import render, redirect
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from .models import Url
import pyshorteners
from .serializers import UrlShortnerSerializer
from rest_framework.decorators import api_view


@api_view(['GET', 'POST', 'DELETE'])
def url_list(request):
    if request.method == 'GET':
        urls = Url.objects.filter(status=1)
        url_serializer = UrlShortnerSerializer(urls, many=True)
        return JsonResponse(url_serializer.data, safe=False)

    elif request.method == 'POST':
        url_data = JSONParser().parse(request)
        if "original_url" in url_data.keys():
            count = Url.objects.filter(original_url=url_data["original_url"],status=0)
            if count:
                Url.objects.filter(original_url=url_data["original_url"], status=0).update(status=1)
                return JsonResponse({'message': 'Existed Inactive URL status marked as 1 and is Active'})
            else:
                short_url = create_short_url(url_data)
                url_data["short_url"] = short_url
                url_serializer = UrlShortnerSerializer(data=url_data)
                if url_serializer.is_valid():
                    url_serializer.save()
                    return JsonResponse(url_serializer.data, status=status.HTTP_201_CREATED)
            return JsonResponse(url_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif "short_url" in url_data.keys():
            urls = Url.objects.filter(short_url=url_data["short_url"],status=1)
            url_serializer = UrlShortnerSerializer(urls,many=True)
            return JsonResponse(url_serializer.data,safe=False, status=status.HTTP_200_OK)
        else:
            url_serializer = UrlShortnerSerializer(data=url_data,many=True)
            return JsonResponse(url_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        url_data = JSONParser().parse(request)
        count = Url.objects.filter(original_url=url_data["original_url"],status=1).update(status=0)
        if count == 1:
            return JsonResponse({'message': '{} URL deleted successfully and status marked as 0'})
        else:
            return JsonResponse({'message': 'URL already deleted'})


def urlRedirect(request, short_url):
    data = Url.objects.get(short_url=short_url)
    return redirect(data.original_url)

def create_short_url(request):
    url = request["original_url"]
    if url.startswith("https://www."):
        url = url.replace("https://www.", "")
    elif url.startswith("http://www."):
        url = url.replace("http://www.", "")
    elif url.startswith("http://"):
        url = url.replace("http://", "")
    elif url.startswith("https://"):
        url = url.replace("https://", "")
    elif url.startswith("www."):
        url = url.replace("www.", "")
    else:
        url = url
    if url.endswith("/"):
        url = url.replace("/", "")
    short_url = pyshorteners.Shortener().tinyurl.short(url)
    return short_url