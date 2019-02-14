import json
import time
import yaml
import pdb
import requests
import time

from InstagramAPI import InstagramAPI
from datetime import datetime
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

# load config
with open('config_scraper.yaml', 'r') as stream:
    try:
        conf = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# neccessary function

def get_str_between(text, str1, str2):
    return text.split(str1)[1].split(str2)[0]

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
                dt = datetime.utcfromtimestamp(older_comment.get('created_at_utc', 0))
                if dt.isoformat() <= self.last_update:
                    comments = [ c for c in comments if datetime.utcfromtimestamp(c.get('created_at_utc', 0)) > until_date]
                    has_more_comments = False
            if has_more_comments:
                max_id = self.api.LastJson.get('next_max_id', '')
                time.sleep(2)

        comments = [{'media_id': media_id, 
                     'created_at': comment['created_at_utc'],
                     'comment_id': comment['pk'],
                     'text': comment['text'],
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
        labels = self.request_label(text, truncate_text=50)

        while not labels:
            print("[E] Error while request labels..")
            labels = self.request_label(text, truncate_text=75)

        for i, label in enumerate(labels):
            comments[i]['label'] = label
        pdb.set_trace()

        return comments


    def set_last_update(self):
        """ 
            Later would be replace by getting last update from DB 
        """
        self.last_update = 0


    def update_last_update(self):
        self.last_update = str(datetime.now())


    def request_label(self, text=[], truncate_text=False, url='http://192.168.38.251:8282/get_classes', slice_text=2, retry=5):
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
                    print("Get~ {}".format(i))

                    i = i + slice_text
                else:
                    if count_retry == 0:
                        temp_labels = self.requst_label_dummy(text[i:i+slice_text])
                        result.extend(temp_labels)
                        count_retry = retry
                        i = i + slice_text

                    count_retry -= 1
                    print("Miss~ {}".format(i))

                time.sleep(2)

            except requests.exceptions.ConnectionError:
                print("Miss~ (ConnectionError)")
                pass    

        return result


    def requst_label_dummy(self, text=[], url=''):
        """ 
            This is dummy function, later it would request to @Geraldi's services
        """
        result = []
        for i in range(len(text)):
            result.append('unlabeled')
        return result


    def send_to_db(self, comments):
        """ 
            @Alson, please implement ssave comments to DB here 
        """
        with open('result.json', 'w') as f:
            f.write(json.dumps(comments))
        pass



if __name__ == '__main__':
    idle_time = conf['UPDATE_EVERY']*60
    w = Wrapper()

    try:
        while True:
            print("[I] Getting comments..".format(idle_time/60))
            comments = []

            # get media id
            media_ids = w.get_media_id_from_user('bukalapak')

            # get comments
            for i, media_id in enumerate(media_ids):
                # print("{}..".format(i))
                comments.extend(w.get_comment_from_media_id(media_id)) # later will used 'until'
                if i == 0:
                    break

            if comments:
                print("[I] request label..".format(idle_time/60))
                comments = w.assign_label(comments)

                print("[I] Save to DB..".format(idle_time/60))

                w.send_to_db(comments)

                w.update_last_update()

            print("[I] Idling for {} minutes..".format(int(idle_time/60)))
            time.sleep(idle_time)
            break
    except KeyboardInterrupt:
        # w.save_set_to_file()
        print("[I] Scrape stopped.")
        pass
