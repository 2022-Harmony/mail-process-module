# mail-process-module
구독자에게 송부할 이메일의 내용을 스크래핑하고, 보내는 모듈

## 분류
- 서브 모듈

## 프로젝트 개요
메인 프로젝트인 news-subscription에서 팀의 클라우드 몽고 db에 저장된 사용자의 이메일과 선호 뉴스 정보를 토대로 관련 뉴스를 스크래핑해 송부함.
스크래핑과 SMTP기술이 이용됌


## 사용 API 
smtp.lib, bs4, pymongo
