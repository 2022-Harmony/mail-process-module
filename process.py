# SMTP 메일 전송 관련
import smtplib  
from email.header import Header
from email.mime.base import MIMEBase # MIME 프로토콜 활용 기능
from email.mime.text import MIMEText # MIME 프로토콜 활용 기능
from email.mime.multipart import MIMEMultipart # MIME 프로토콜 활용 기능
from email import utils
from email import encoders
from email.utils import COMMASPACE
import os
import settings
import time


#크롤링 관련
import requests
from bs4 import BeautifulSoup
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}

#DB 관련
from pymongo import MongoClient
from DB_ADMIN import mongo_admin
db = mongo_admin.mongo_connector()


## Done ##
def today_news_url_update():
    '''
        오늘 전송할 뉴스의 url과 분야 정보를 수집하는 스크래핑 모듈,  타 메서드와 관계성 X
    '''
    detect_list = ['POLITICS_DIC_URL', 'ECONOMY_DIC_URL', 'SOCIETY_DIC_URL', 'SCIENCE_DIC_URL', 'WORLD_DIC_URL']
    type_list = ['politics_type', 'economy_type', 'society_type', 'science_type', 'world_type']
    db.today_news_url.delete_many({}) #어제 news 다 지워주고
    
    for target, type in zip(detect_list, type_list):
        data = requests.get(settings.ABOUT_URL_DIC[target], headers=headers)
        soup = BeautifulSoup(data.text, 'html.parser')
        news_list = soup.select('#main_content > div > div._persist > div:nth-child(1) > div')
        for news in news_list: # 해당 janr의 news_list url 수집해 db에 update
            news_html = news.select_one('div.cluster_body > ul > li:nth-child(1) > div.cluster_thumb > div > a')
            # print(news_html.attrs['href'])

            try: # url 정보를 db에 update
                docs = {'news_detail_url': news_html.attrs['href'], 'url_janr': settings.ABOUT_URL_DIC[type]}
                db.today_news_url.insert_one(docs)
                #print('OK: today news url update')
            except:
                try:
                    news_html = news.select_one('div.cluster_body > ul > li:nth-child(1) > div.cluster_thumb > div > a')
                    docs = {'news_detail_url': news_html.attrs['href'], 'url_janr': settings.ABOUT_URL_DIC[type]}
                    db.today_news_url.insert_one(docs)
                except:
                    print('Error: lost url {}'.format(docs['news_detail_url']))



## Done ##
def get_news_detail():
    '''
        스크래핑 모듈에서 수집한 url 기반으로 뉴스의 제목, 본문 데이터 수집하는 모듈, 타 메서드와 관계성 X
    '''
    
    db.today_news_url.delete_many({}) #어제 news 내용 다 지워주고
    
    news_urls = list(db.today_news_url.find({}, {'_id': False, 'url_janr': 0}))
    news_janr = list(db.today_news_url.find({}, {'_id': False, 'news_detail_url': 0}))
    for url, janr in zip(news_urls, news_janr):
#        print(url['news_detail_url'])
        data = requests.get(url['news_detail_url'], headers=headers)
        soup = BeautifulSoup(data.text, 'html.parser')
        article_title = soup.select_one('#articleTitle').get_text()
        article_text = soup.select_one('#articleBodyContents').get_text()
        
        docs = {'articleTitle': article_title, 'articleText': article_text, 'janr': janr['url_janr']}
        db.news_detail_info.insert_one(docs)
        

## In Progress##
def send_email_all_users(current_time):
    '''
        구독자에게 메일 전송을 하기 위해 오늘의 뉴스 정보를 분야별로 분류, 분류된 뉴스 정보와 각 사용자의 선호정보를 묶어 
        send_news_each_user 전달함, 연관: send_news_each_user
    '''
    
    politics_news  = db.news_detail_info.find_one({'janr': '정치'}, {'_id': False, 'url_janr': 0})
    economy_news  = db.news_detail_info.find_one({'janr': '경제'}, {'_id': False, 'url_janr': 0})
    society_news  = db.news_detail_info.find_one({'janr': '사회'}, {'_id': False, 'url_janr': 0})
    science_news  = db.news_detail_info.find_one({'janr': '과학'}, {'_id': False, 'url_janr': 0})
    world_news  = db.news_detail_info.find_one({'janr': '세계'}, {'_id': False, 'url_janr': 0})
    
    sending_news_pakage = {'정치': politics_news, '경제': economy_news, '사회': society_news, '과학': science_news, '세계': world_news}
    # print(politics_news, "\n\n", economy_news, "\n\n", society_news, "\n\n", science_news, "\n\n", world_news)

    
    # 사용자 정보 받아오기
    # subscription_info_list = list(db.subscription_admin.find({'delivery_time': current_time}, {'_id': False}))
    subscription_info_list = list(db.subscription_admin.find({}, {'_id': False}))
    
    maching_news = []
    
    for subscription_info in subscription_info_list:
        to_users = subscription_info['user_email']
        subscription_type = subscription_info['subscription_type']
        maching_news.append(to_users+'$#$'+subscription_type)
    send_news_each_user(maching_news, sending_news_pakage)



def send_news_each_user(maching_news, sending_news_pakage):
    '''
        한번에 전송할 수 있게 각 구독자의 선호정보를 분류해서 일괄적으로 묶은 뒤 
        GSMTP를 이용해 메일을 전송하는 send_email_users에게 넘겨줌. 연관: send_email_users
    '''
    pol_user = []
    eco_user = []
    soc_user = []
    sci_user = []
    wolrd_user = []
    
    cc_users = []
    
    
    for each in maching_news:
        if each.split('$#$')[1] == '정치':
            pol_user.append(each.split('$#$')[0])

        elif each.split('$#$')[1] == '경제':
            eco_user.append(each.split('$#$')[0])

        elif each.split('$#$')[1] == '사회':
            soc_user.append(each.split('$#$')[0])

        elif each.split('$#$')[1] == 'IT/과학':
            sci_user.append(each.split('$#$')[0])
        
        elif each.split('$#$')[1] == '세계':
            wolrd_user.append(each.split('$#$')[0])

    #정치 관련 메일 전송
    send_email_users(settings.GMAILID, pol_user, cc_users, ('[구독하신 정치 관련 뉴스]'+sending_news_pakage['정치']['articleTitle']), sending_news_pakage['정치']['articleText'].replace('.', '<br>'), 'html')
    send_email_users(settings.GMAILID, eco_user, cc_users, ('[구독하신 경제 관련 뉴스]'+sending_news_pakage['경제']['articleTitle']), sending_news_pakage['경제']['articleText'].replace('.', '<br>'), 'html')
    send_email_users(settings.GMAILID, soc_user, cc_users, ('[구독하신 사회 관련 뉴스]'+sending_news_pakage['사회']['articleTitle']), sending_news_pakage['사회']['articleText'].replace('.', '<br>'), 'html')
    send_email_users(settings.GMAILID, sci_user, cc_users, ('[구독하신 과학 관련 뉴스]'+sending_news_pakage['과학']['articleTitle']), sending_news_pakage['과학']['articleText'].replace('.', '<br>'), 'html')
    send_email_users(settings.GMAILID, wolrd_user, cc_users, ('[구독하신 세계 관련 뉴스]'+sending_news_pakage['세계']['articleTitle']), sending_news_pakage['세계']['articleText'].replace('.', '<br>'), 'html')
    
    


 ## In Progress ##
def send_email_users(from_user, to_users, cc_users, subject, text, text_format='plain', smtp_server='smtp.gmail.com', smtp_port=587):
    '''
        실질적으로 메일을 전송하는 함수, 
        각 분야의 신문들을 사용자들에게 일괄 분배
    '''
    
    for user in to_users:
        msg = MIMEMultipart('multipart')
        msg['FROM'] = from_user               
        msg['To'] = user
        msg['Subject'] = Header(s=subject, charset='utf-8') 
        msg['Date'] = utils.formatdate(localtime=1)  

        part = MIMEText(text, text_format)     
        msg.attach(part)                             

        try: 
            server = smtplib.SMTP(smtp_server, smtp_port)
            try:  
                server.ehlo()
                server.starttls()
                server.login(settings.GMAILID, settings.GMAILPW)
                server.sendmail(msg['FROM'], [msg['To']], msg.as_string())
                print("[Success] send mail: " + msg['To'])
                print(msg['Subject'])
            except:
                print("[Fail] send mail: " +type(msg['To']))
                print("[Error] Fail to send mail")

            finally:
                server.quit()  # smtp 연결 종료
        except:
            print("[Error] Fail to connect")
            return False
    
    