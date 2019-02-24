# SETUP_DJANGO, ADD PARENT DIR
import django
import inspect
import sys
import os
import os.path
import yaml

# LOAD CONFIG
with open('julid/config_scraper.yaml', 'r') as stream:
    try:
        conf = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# ADD PARENT DIR

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

if conf['DATABASE_SAVE_COMPLAINT'] == 'MYSQL':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'settings')
    django.setup()
    from trello.label import Label
    from trel import enums as e
    from trel import global_variables as g
    from trel.models import Complaint
elif conf['DATABASE_SAVE_COMPLAINT'] == 'FILE':
    import pickle

import json
import time
import pdb
import requests
import time
import pytz

from InstagramAPI import InstagramAPI
from datetime import datetime
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

tz = pytz.timezone('Pacific/Johnston')

# NECCESSARY FUNCTION

def prefix_media_id(text, media_id):
    try:
        text = '[media_id: {}] {}'.format(media_id.split('_')[0], text)
    except:
        text = text
    return text

def get_str_between(text, str1, str2):
    return text.split(str1)[1].split(str2)[0]

def exclude_weird_character(text):
    new_text = ''
    for char in text:
        if ord(char) >= 0 and ord(char) < 256:
            new_text += char
    return new_text

def get_url_from_media_id(post_or_media_id):
    prefix = "https://www.instagram.com/p/";
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    suffix = ''

    try:
        if '_' in post_or_media_id:
            post_id = int(post_or_media_id.split('_')[0])
        else:
            post_id = int(post_or_media_id)

        while(post_id > 0):
            remainder = int(post_id % 64)
            post_id = (post_id - remainder) / 64
            suffix = alphabet[remainder] + suffix
    except Exception:
        return '<invalid media_id: {}>'.format(media_id)

    return prefix + suffix

def printl(text, type_='i'):
    if conf['PRINT_LOG']:
        print('[{}] {} -- {}'.format(type_.upper(), datetime.now().replace(microsecond=0).isoformat(' '), text))

def add_card_to_trello(complaint): # complaint is a comment
    if not conf['REQUEST_ADD_CARD_TO_TRELLO']:
        return
    name = '@{}: "{}"'.format(complaint['username'], complaint['text'])
    desc = 'Post : {}'.format(get_url_from_media_id(complaint['post_id']))
    labels = [g.labels[complaint['category']]]
    position = 'top'

    card = g.list_complaints.add_card(name, desc=desc, labels=labels, position=position)
    return card

DUMMY = {
    'username': conf['IG_USERNAME'],
    'text': conf['DUMMY_TEXT'],
    'category': 'other',
    'media_id': '------------------------------'
}

# -----------------------------------------------------------


class Wrapper(object):
    def __init__(self):
        self.api = InstagramAPI(conf['IG_USERNAME'], conf['IG_PASS'])
        self.api.login()
        self.api.getUsernameInfo(str(conf['IG_USER_ID']))
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
                if dt >= self.last_update:
                    comments = [ c for c in comments 
                                 if datetime.utcfromtimestamp(c.get('created_at_utc', 0)).isoformat() > self.last_update]
                    has_more_comments = False
            if has_more_comments:
                max_id = self.api.LastJson.get('next_max_id', '')
                # time.sleep(0)

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


        # the json data is between this shitty strings
        substring1 = '<script type="text/javascript">window._sharedData = '
        substring2 = ';</script>'

        data = soup.find_all('script')[4]
        data = get_str_between(str(soup.find_all('script')[4]), substring1, substring2)
        data = json.loads(data)

        media_ids = []

        i = 0
        user_id = data['entry_data']['ProfilePage'][0]['graphql']['user']['id']

        while True:
            try:
                media_id = data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges'][i]['node']['id']
                timestamp = data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges'][i]['node']['taken_at_timestamp']
                media_ids.append({'media_id': media_id, 'timestamp': timestamp})
                i += 1
            except IndexError:
                break

        for i, media_id in enumerate(media_ids):
            media_ids[i]['media_id'] = '{}_{}'.format(media_id['media_id'], user_id)

        return media_ids


    def assign_label(self, comments, media_id):
        text = [comment['text'] for comment in comments]

        if not text:
            return []
        labels = self.request_label(text, media_id=media_id)

        while not labels:
            printl(prefix_media_id("Requesting label incomplete, retry", media_id))
            labels = self.request_label(text, media_id=media_id)

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
        printl('Last update checkpoint: {}'.format(self.last_update))


    def request_label(self, text = [], 
                            media_id = '<unassigned>', 
                            truncate_text = False, 
                            url = conf['REQUEST_LABEL_URL'],
                            slice_text = conf['REQUEST_LABEL_SLICE_PER'], 
                            retry = 3):
        result = []
        i = 0
        count_retry = retry

        slice_text = min(slice_text, len(text))

        if truncate_text:
            text = [line[0:truncate_text] for line in text]

        while True:
            if i > len(text):
                break
            try:
                if len(text[i:i+slice_text]) <= 0 :
                    break
                response = requests.post(url, json = {'texts': text[i:i+slice_text]}, 
                                              headers = {"Content-Type":"application/json"})

                if response.ok:
                    response_data = json.loads(response._content)
                    temp_labels = response_data['data']['labels']

                    count_retry = retry
                    result.extend(temp_labels)
                    printl(prefix_media_id("Request label to {}: SUCCESS ({}/{})".format(url, i, len(text)), media_id))

                    i = i + slice_text
                else:
                    if count_retry == 0:
                        temp_labels = self.assign_unknown(text[i:i+slice_text])
                        result.extend(temp_labels)
                        count_retry = retry
                        i = i + slice_text
                        printl(prefix_media_id("Label Request Failed, Assign 'unknown' ({}/{}), retry ({})".format(i, len(text), count_retry), media_id))
                    else:
                        count_retry -= 1
                        printl(prefix_media_id("Label Request Failed.. ({}/{}), retry ({})".format(i, len(text), count_retry), media_id))
                        # time.sleep(1.6)

                # time.sleep(0.1)

            except requests.exceptions.ConnectionError:
                printl("Miss~ (ConnectionError)")
                pass    

        return result

    def save_complaints(self, comments, check_comment_id=True):
        for comment in comments:
            self.save_complaint(comment)

    def add_complaints_to_trello(self, complaints):
        count = 0
        for i, complaint in enumerate(complaints):
            if complaint['category'].lower() in ['unknown', 'lainnya', 'other']:
                continue
            card = add_card_to_trello(complaint)
            complaints[i]['trello_id'] = card.id
            count += 1
        return count

    def save_complaint(self, complaint): # comments is dictionary
        default_complaint = { 
                                'text': '-----',
                                'state': 0,
                                'category': 'other',
                                'username': '-----',
                                'post_id': '0',
                                'comment_id': '0',
                                'ready_at': datetime.now(tz=tz),
                                'wip_at': None,
                                'resolved_at': None,
                                'trello_id': None
                            }


        for key, value in default_complaint.items():
            if key not in complaint:
                complaint[key] = default_complaint[key]

        if conf['DATABASE_SAVE_COMPLAINT'] == 'MYSQL':
            Complaint.objects.create(text= complaint['text'],
                                     state= complaint['state'],
                                     category= complaint['category'],
                                     username= complaint['username'],
                                     instagram_post_id= complaint['post_id'],
                                     instagram_comment_id= complaint['comment_id'],
                                     ready_at= complaint['ready_at'],
                                     wip_at= complaint['wip_at'],
                                     resolved_at= complaint['resolved_at'],
                                     trello_id=complaint['trello_id'])

        elif conf['DATABASE_SAVE_COMPLAINT'] == 'FILE':
            with open('{}{}.pkl'.format(conf['DATABASE_PREFIX_COMPLAINT_FILE'], complaint['comment_id']), 'wb') as outfile:  
                pickle.dump(complaint, outfile)


    def filter_comments(self, comments):
        # filter the comment if it already exist in database or not
        r = []
        for comment in comments:
            if not self.already_exist(comment):
                r.append(comment)
        return r

    def already_exist(self, comment):
        if conf['DATABASE_SAVE_COMPLAINT'] == 'MYSQL':
            if Complaint.objects.filter(instagram_comment_id=comment['comment_id']).exists():
                return True
            else:
                return False

        if conf['DATABASE_SAVE_COMPLAINT'] == 'FILE':
            if os.path.isfile('{}{}.json'.format(conf['DATABASE_PREFIX_COMPLAINT_FILE'], comment['comment_id'])):
                return True
            else:
                return False

    def assign_unknown(self, text=[], url=''):
        """ 
            Assign 'unknown' label. Used if failed to request label to @Geraldi's services
        """
        result = []
        for i in range(len(text)):
            result.append('unknown')
        return result

    def run_for_media_id(self, media_id, is_return_comments=False):
        printl(prefix_media_id("Getting comment(s)", media_id))
        comments = self.get_comment_from_media_id(media_id, count=100) # later will used 'until'
        printl(prefix_media_id("Got {} comment(s)".format(len(comments)), media_id))

        if comments:
            printl(prefix_media_id("Filtering {} comment(s)..".format(len(comments)), media_id))
            comments = self.filter_comments(comments) # filter the comment that already exist
            printl(prefix_media_id("Comments filtered, got {} comment(s)".format(len(comments)), media_id))
        else: # check if still exist
            printl(prefix_media_id("Got no new comments", media_id))
            return

        printl(prefix_media_id("Requesting label to {} ({} comments)".format(conf['REQUEST_LABEL_URL'], len(comments)), media_id))
        comments = self.assign_label(comments, media_id=media_id)
        printl(prefix_media_id("Request label to {} ({} comments) done".format(conf['REQUEST_LABEL_URL'], len(comments)), media_id))

        printl(prefix_media_id("Adding comment(s) to trello..".format(conf['REQUEST_LABEL_URL'], len(comments)), media_id))
        number_of_complaint_added_to_trello = self.add_complaints_to_trello(comments)
        printl(prefix_media_id("There are {} complaint out of {} comments added to trello".format(number_of_complaint_added_to_trello, len(comments)), media_id))

        # with open('for_debug.json', 'w') as file:
        #     json.dump(comments, file, indent=4)

        printl(prefix_media_id("Saving {} comment(s) to database..".format(len(comments)), media_id))
        self.save_complaints(comments)
        printl(prefix_media_id("{} comment(s) saved to database.".format(len(comments)), media_id))

        return comments if is_return_comments else True



# ---------------------------------------------------------------------------------------------------------


w = Wrapper()
user_to_scrap = conf['IG_USER_TO_SCRAPPED']

# Just go function

def forever_run():
    try:
        while True:
            checkpoint = datetime.now()

            comments = []

            # get media id
            printl('Getting media_id from @{}'.format(user_to_scrap))
            media_ids = w.get_media_id_from_user(user_to_scrap)

            # for every media_id, get comments
            for i, media_id in enumerate(media_ids):
                if i >= conf['MONITORED_N_LAST_MEDIA_ID']:
                    break
                w.run_for_media_id(media_id['media_id'])
                if i + 1 != len(media_ids):
                    printl("Go to the next media_id")

            w.update_last_update(checkpoint)

            printl("Idle for {} seconds..".format(conf['RUNNING_IDLE_TIME']))

            time.sleep(conf['RUNNING_IDLE_TIME'])
    except KeyboardInterrupt:
        printl("Scrape stopped.")
        pass

def scrape_and_save_for_media_id(media_id):
    checkpoint = datetime.now()
    w.run_for_media_id(media_id)
    w.update_last_update(checkpoint)

def scrape_and_save_for_media_ids(media_ids):
    checkpoint = datetime.now()
    for media_id in media_ids:
        w.run_for_media_id(media_id)
    w.update_last_update(checkpoint)

def update_media_ids():
    printl('Updating media ids..')
    new_media_ids = w.get_media_id_from_user(user_to_scrap)

    # read file first
    try:
        with open(conf['MEDIA_ID_SAVE_FILE']) as json_file:  
            media_ids = json.load(json_file)
    except Exception as e:
        printl('{} file not found, rewrite.'.format(conf['MEDIA_ID_SAVE_FILE']), type_='w')
        media_ids = []
        pass

    # check new media_id
    for new_media_id in new_media_ids:
        new = True
        for media_id in media_ids:
            if new_media_id['media_id'] == media_id['media_id']:
                new = False
                break
        if new:
            media_ids.append(new_media_id)

    # sort
    media_ids = sorted(media_ids, key=lambda k: k['timestamp'], reverse=True) 

    # write again
    with open(conf['MEDIA_ID_SAVE_FILE'], 'w') as json_file:  
        json.dump(media_ids, json_file, indent=4)

    r = []
    for media_id in media_ids:
        r.append(media_id['media_id'])
    media_ids = r

    return media_ids

def get_n_last_media_ids(n=conf['MONITORED_N_LAST_MEDIA_ID'], update_first=False):
    if update_first:
        media_ids = update_media_ids()
    else:
        with open(conf['MEDIA_ID_SAVE_FILE']) as json_file:  
            media_ids = json.load(json_file)
        r = []
        for media_id in media_ids:
            r.append(media_id['media_id'])
        media_ids = r

    return media_ids[0:n]

if __name__ == '__main__':
    # c1 = update_media_ids()
    # c2 = get_n_last_media_ids()
    # scrape_and_save_for_media_id(c1[0])
    # scrape_and_save_for_media_ids(c1[1:3])
    forever_run()
    # pdb.set_trace()
    pass