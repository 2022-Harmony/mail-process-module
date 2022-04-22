from pymongo import MongoClient
from DB_ADMIN import account


def mongo_connector(): # 보안을 위해 몽고DB Client Connect하는 함수 별도 생성
    client = MongoClient(account.API_KEY)
    return client.Haromony