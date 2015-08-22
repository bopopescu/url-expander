from django.db import models
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from mysite import settings
# GG imports
import requests
import bs4
from selenium import webdriver
import os


# Create your models here.
class Url(models.Model):
    original = models.URLField()
    destination = models.URLField()
    httpstatus = models.IntegerField()
    title = models.TextField()
    screenshot = models.URLField()

    def make(self):
        r = requests.get(self.original)
        self.destination = r.url
        self.httpstatus = r.status_code
        self.title = bs4.BeautifulSoup(r.text).title.text
        driver = webdriver.PhantomJS(service_log_path=os.path.devnull)
        driver.get(self.destination)
        filename = self.title.replace(' ', '')
        driver.save_screenshot('/tmp/'+filename+'.png')
        driver.quit()
        conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        b = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        k = Key(b)
        k.key = '/screenshots/' + filename + '.png'
        k.set_contents_from_filename('/tmp/' + filename + '.png')
        b.set_acl('public-read', '/screenshots/' + filename + '.png')
        os.remove('/tmp/' + filename + '.png')
        self.screenshot = 'https://s3.amazonaws.com/gegray-bucket-lab3/screenshots/' + filename + '.png'
        self.save()
