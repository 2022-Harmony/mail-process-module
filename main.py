import process

def main():
    current_time = "11" #test용 현재 시간
    # 정치, 경제, 사회, 과학, 세계에 대한 오늘의 뉴스 url db에 업데이트
    # process.today_news_url_update()  #1. 오늘 배부할 news url 정보 수집
    # process.get_news_detail()        #2. 수집한 news url의 주소로 접근해 news의 세부 내용 수집
    process.send_email_all_users(current_time)   #3. 수집한 news 내용을 사용자 mail로 전송

if __name__ == "__main__":
    main()