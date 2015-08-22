from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import login_required
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from mysite import settings
from selenium import webdriver
from ratelimit.decorators import ratelimit
import os

# GG imports
from .models import Url
from .forms import UrlForm
from .serializers import UrlSerializer


# Create your views here.
@ratelimit(key='ip', rate='10/m', block=True)
@login_required(login_url='/urlexpander/accounts/login/')
def url_list(request):
    urls = Url.objects.all()
    return render(request, 'urlexpander/url_list.html', {'urls': urls})


@ratelimit(key='ip', rate='10/m', block=True)
@login_required(login_url='/urlexpander/accounts/login/')
def url_detail(request, pk):
    url = get_object_or_404(Url, pk=pk)
    if request.POST.get('delete'):
        url.delete()
        return redirect('urlexpander.views.url_list')
    elif request.POST.get('recap'):
        refresh_screenshot(request, pk)
    return render(request, 'urlexpander/url_detail.html', {'url': url})


@ratelimit(key='ip', rate='10/m', block=True)
@login_required(login_url='/urlexpander/accounts/login/')
def url_add(request):
    if request.method == "POST":
        form = UrlForm(request.POST)
        if form.is_valid():
            url = form.save(commit=False)
            url.make()
            url.save()
            return redirect('urlexpander.views.url_detail', pk=url.pk)
    else:
        form = UrlForm()

    return render(request, 'urlexpander/url_add.html', {'form': form})


@ratelimit(key='ip', rate='10/m', block=True)
@login_required(login_url='/urlexpander/accounts/login/')
def url_remove(request, pk):
    url = get_object_or_404(Url, pk=pk)
    url.delete()
    filename = url.title.replace(' ', '')
    conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
    key = Key(bucket)
    key.key = '/screenshots/'+filename+'.png'
    bucket.delete_key(key)
    return redirect('urlexpander.views.url_list')


@ratelimit(key='ip', rate='10/m', block=True)
@login_required(login_url='/urlexpander/accounts/login/')
@api_view(['GET', 'POST'])
def api_url_list(request, format=None):
    if request.method == 'GET':
        urls = Url.objects.all()
        serializer = UrlSerializer(urls, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = UrlSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@ratelimit(key='ip', rate='10/m', block=True)
@login_required(login_url='/urlexpander/accounts/login/')
@api_view(['GET', 'PUT', 'DELETE'])
def api_url_detail(request, pk, format=None):
    try:
        url = Url.objects.get(pk=pk)
    except Url.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UrlSerializer(url)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UrlSerializer(url, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        url.delete()
        filename = url.title.replace(' ', '')
        conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        key = Key(bucket)
        key.key = '/screenshots/'+filename+'.png'
        bucket.delete_key(key)
        return Response(status=status.HTTP_204_NO_CONTENT)


@ratelimit(key='ip', rate='10/m', block=True)
@login_required(login_url='/urlexpander/accounts/login/')
@api_view(['POST'])
def refresh_screenshot(request, pk, format=None):
    url = get_object_or_404(Url, pk=pk)
    if request.method == 'POST':
        driver = webdriver.PhantomJS(service_log_path=os.path.devnull)
        driver.get(url.destination)
        filename = url.title.replace(' ', '')
        driver.save_screenshot('/tmp/'+filename+'.png')
        driver.quit()
        conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY )
        b = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        k = Key(b)
        k.key = '/screenshots/' + filename + '.png'
        k.set_contents_from_filename('/tmp/' + filename + '.png')
        b.set_acl('public-read', '/screenshots/' + filename + '.png')
        os.remove('/tmp/' + filename + '.png')
        url.screenshot = 'https://s3.amazonaws.com/gegray-bucket-lab3/screenshots/' + filename + '.png'
