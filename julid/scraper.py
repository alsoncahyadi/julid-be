import json
import time
import yaml
import pdb
import requests
import time
import os
import sys
import inspect
import django

from InstagramAPI import InstagramAPI
from datetime import datetime
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import pytz


tz = pytz.timezone('Pacific/Johnston')

# setup django
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'settings')
sys.path.insert(0,parentdir) 
django.setup()

from trello.models import Complaint

# load config
with open('julid/config_scraper.yaml', 'r') as stream:
    try:
        conf = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# neccessary function

def get_str_between(text, str1, str2):
    return text.split(str1)[1].split(str2)[0]

def exclude_weird_character(text):
    new_text = ''
    for char in text:
        if ord(char) >= 0 and ord(char) < 256:
            new_text += char
    return new_text



# media_id = '1978173529828450686_1460855092'
class Wrapper(object):
    def __init__(self):
        self.api = InstagramAPI(conf['USERNAME'], conf['PASS'])
        self.api.login()
        self.api.getUsernameInfo(str(conf['USERID']))
        self.set_last_update()


    def get_comment_from_media_id(self, media_id, count=100):
        has_more_comments = True
        comments = []
        max_id = ''
        
        while has_more_comments:
            _ = self.api.getMediaComments(media_id, max_id=max_id)
            for c in reversed(self.api.LastJson['comments']):
                comments.append(c)
            has_more_comments = self.api.LastJson.get('has_more_comments', False)
            if count and len(comments) >= count:
                comments = comments[:count]
                has_more_comments = False
            if self.last_update:
                older_comment = comments[-1]
                dt = datetime.utcfromtimestamp(older_comment.get('created_at_utc', 0)).isoformat()
                if dt <= self.last_update:
                    comments = [ c for c in comments if datetime.utcfromtimestamp(c.get('created_at_utc', 0)).isoformat() > self.last_update]
                    has_more_comments = False
            if has_more_comments:
                max_id = self.api.LastJson.get('next_max_id', '')
                time.sleep(1)

        comments = [{'post_id': media_id, # media_id
                     'created_at': comment['created_at_utc'],
                     'comment_id': comment['pk'],
                     'text': exclude_weird_character(comment['text']),
                     'username': comment['user']['username']} for comment in comments]

        return comments


    def get_media_id_from_user(self, username, retry=5):
        url = 'https://www.instagram.com/{}'.format(username)
        all_review_content = []
        try:
            page = urlopen(Request(url, headers={'User-Agent': 'Chrome'}))
            content = page.read()
        except Exception as e:
            if not retry:
                retry -= 1
            else:
                raise Exception("Cannot get the instagram page")

        soup = BeautifulSoup(content, 'html.parser')

        data = soup.find_all('script')[4]
        data = get_str_between(str(soup.find_all('script')[4]), '<script type="text/javascript">window._sharedData = ', ';</script>')
        data = json.loads(data)

        media_ids = []

        i = 0
        user_id = data['entry_data']['ProfilePage'][0]['graphql']['user']['id']
        while True:
            try:
                media_id = data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges'][i]['node']['id']
                media_ids.append(media_id)
                i += 1
            except IndexError:
                break

        media_ids = ['{}_{}'.format(media_id, user_id) for media_id in media_ids]

        return media_ids


    def assign_label(self, comments):
        text = [comment['text'] for comment in comments]

        if not text:
            return []
        labels = self.request_label(text, truncate_text=50)

        while not labels:
            print("[E] Error while request labels..")
            labels = self.request_label(text, truncate_text=75)

        for i, label in enumerate(labels):
            comments[i]['category'] = label

        return comments


    def set_last_update(self):
        """ 
            Later would be replace by getting last update from DB 
        """
        self.last_update = 0


    def update_last_update(self, time_=None):
        if time_ is None:
            self.last_update = time_.isoformat()
        else:
            self.last_update = datetime.now().isoformat()


    def request_label(self, text=[], truncate_text=False, url='http://192.168.38.251:8282/get_classes', slice_text=10, retry=10):
        result = []
        i = 0
        count_retry = retry

        if truncate_text:
            text = [line[0:truncate_text] for line in text]

        while True:
            if i > len(text):
                break
            try:
                response = requests.post(url, json={'texts': text[i:i+slice_text]}, 
                                              headers={"Content-Type":"application/json"}, 
                                              timeout=1000)

                if response.ok:
                    response_data = json.loads(response._content)
                    temp_labels = response_data['data']['labels']

                    count_retry = retry
                    result.extend(temp_labels)
                    print("[I] Get~ ({}/{})".format(i, len(text)))

                    i = i + slice_text
                else:
                    if count_retry == 0:
                        temp_labels = self.requst_label_dummy(text[i:i+slice_text])
                        result.extend(temp_labels)
                        count_retry = retry
                        i = i + slice_text
                        print("[I] Miss~ ({}/{}), retry ({})".format(i, len(text), count_retry))
                    else:
                        count_retry -= 1
                        print("[I] Miss~ ({}/{}), retry ({})".format(i, len(text), count_retry), end='\r')
                        time.sleep(1.6)

                time.sleep(0.1)

            except requests.exceptions.ConnectionError:
                print("Miss~ (ConnectionError)")
                pass    

        return result

    def save_complaints(self, comments, check_comment_id=True):
        for comment in comments:
            self.save_complaint(comment)

    def save_complaint(self, complaint): # comments is dictionary
        default_complaint = { 
                                'text': '-----',
                                'state': 0,
                                'category': 'other',
                                'username': '-----',
                                'post_id': '0',
                                'comment_id': '0',
                                'ready_at': datetime.now(tz=tz),
                                'wip_at': datetime.now(tz=tz),
                                'resolved_at': datetime.now(tz=tz)
                            }

        for key, value in default_complaint.items():
            if key not in complaint:
                complaint[key] = default_complaint[key]

        Complaint.objects.create(text= complaint['text'],
                                 state= complaint['state'],
                                 category= complaint['category'],
                                 username= complaint['username'],
                                 post_id= complaint['post_id'],
                                 comment_id= complaint['comment_id'],
                                 ready_at= complaint['ready_at'],
                                 wip_at= complaint['wip_at'],
                                 resolved_at= complaint['resolved_at'])

    def filter_comments(self, comments):
        # filter the comment if it already exist in database or not
        r = []
        for comment in comments:
            if not Complaint.objects.filter(comment_id= comment['comment_id']).exists():
                r.append(comment)
        return r

    def requst_label_dummy(self, text=[], url=''):
        """ 
            This is dummy function, later it would request to @Geraldi's services
        """
        result = []
        for i in range(len(text)):
            result.append('unknown')
        return result


    def send_to_db(self, comments):
        """ 
            Deprecated
            @Alson, please implement ssave comments to DB here 
        """

        with open('result.json', 'w') as f:
            f.write(json.dumps(comments))
        pass




if __name__ == '__main__':
    idle_time = conf['UPDATE_EVERY']*60
    w = Wrapper()
    user_to_scrap = 'bukalapak'

    try:
        while True:
            checkpoint = datetime.now()

            comments = []

            # get media id
            print('[I] Getting media_id from @{}'.format(user_to_scrap))
            media_ids = w.get_media_id_from_user(user_to_scrap)

            # get comments
            for i, media_id in enumerate(media_ids):
                # print("{}..".format(i))
                print("[I] Getting comments, media_id: {}".format(media_id))
                comments = w.get_comment_from_media_id(media_id, 10000) # later will used 'until'

                if comments:
                    print("[I] Filter comments..")
                    comments = w.filter_comments(comments) # filter the comment that already exist
                
                if comments:
                    print("[I] Requesting label..")
                    comments = w.assign_label(comments)

                    print("[I] Saving to DB..")
                    w.save_complaints(comments)
                else:
                    print("[W] The post with media_id:{} has no new comments".format(media_id))

            w.update_last_update(checkpoint)

            print("[I] Idle for {} minutes..".format(int(idle_time/60)))
            time.sleep(idle_time)
    except KeyboardInterrupt:
        # w.save_set_to_file()
        print("[I] Scrape stopped.")
        pass
