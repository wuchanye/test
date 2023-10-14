from flask import request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from opencc import OpenCC
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from io import BytesIO
from PIL import Image
import pyimgur
import urllib.request as urllib_request
import urllib.parse as parse
import json
import time
import os
import requests
import re
import base64


from flask import Flask
app = Flask(__name__)

line_bot_api=LineBotApi('h3KUlT/r7nBj0F1L7SiDJf4e809FD64XLazi5LGtx7ch3LhjtqiqA0Mx4RDHGPm/VUNOkNqqqNQO/TJnj/sx1OQU+j2KlmGsgAQG3R0GG00Z47xrW2kYla+V4wFrt5WZ9Ku612SwHFVtAnGMzkMeZgdB04t89/1O/w1cDnyilFU=')
handler=WebhookHandler('d433242811b1a47be485a3068a7318d1') 


@app.route("/callback" , methods = ['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

WAITING_FOR_FOOD_NAME = 1
WAITING_FOR_QUERY_NUM = 2
WAITING_FOR_IMG = 3
NORMAL = 0
current_state = None
search_results = []

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    global current_state
    global keyword
    global search_results
    global img_path
    
    if current_state == WAITING_FOR_FOOD_NAME:
        keyword = user_message  # 將用戶的回覆儲存在 keyword 變數中
        current_state = NORMAL  # 回復正常狀態
        search_results, messages = search(keyword)
        
        if search_results:  # 不是空列表，即有搜尋結果
            current_state = WAITING_FOR_QUERY_NUM
            title = '請選擇想查詢的食物代號：\n'
            for i in range(len(messages) - 1, 0, -1):
                messages[i] = messages[i - 1]
            messages[0] = title
            messages_text = "\n".join(messages)
            
            message = TextSendMessage(messages_text)
            line_bot_api.reply_message(event.reply_token, message)
            
        
    elif current_state == WAITING_FOR_QUERY_NUM:
        if search_results:
            try:
                messages = []
                query_number = int(user_message)
                img_keyword, message = query(query_number, search_results)
                
                github_repo = 'wuchanye/test'
                github_path = 'imgs2/' + img_keyword + '.jpg'
                github_token = os.environ.get('github_token')
                img_path = download_images_and_upload_to_github(1, img_keyword, github_repo,github_path, github_token)
                img_message = upload_image_to_github(img_path, github_repo, github_path, github_token)

                messages = [message , img_message]
                line_bot_api.reply_message(event.reply_token, messages)
                
            except ValueError:
                message = TextSendMessage(text='請輸入有效的數字。')
                line_bot_api.reply_message(event.reply_token, message)
                current_state = NORMAL
            
            
    else:
        if user_message == ("@查詢"):
            current_state = WAITING_FOR_FOOD_NAME
            message = TextSendMessage(text='請輸入食物名稱：')
            line_bot_api.reply_message(event.reply_token, message)
                    
            
#搜尋食物 獲取食物名稱,foodId
def search(keyword):
    messages = []
    m=1
    
    # 繁體中文關鍵字
    encoded_keyword_traditional = parse.quote(keyword)
    t2s = OpenCC('t2s') #繁轉簡
    s2t = OpenCC('s2t') #簡轉繁
    simplified_name = t2s.convert(keyword)
    # 簡體中文關鍵字
    encoded_keyword_simplified = parse.quote(simplified_name)
    
    data_simplified = {} #解決繁簡相同時 未賦予值的問題

    while True:
        # 繁簡相異
        if encoded_keyword_traditional != encoded_keyword_simplified:
            # app_id=uxnxyhgkujxpgqbt&app_secret=UHJqRjR6S25DaSttRWxZUElSbnovUT09
            # 搜尋繁體中文資料
            url_traditional = f"https://www.mxnzp.com/api/food_heat/food/search?keyword={encoded_keyword_traditional}&page={m}&app_id=uxnxyhgkujxpgqbt&app_secret=UHJqRjR6S25DaSttRWxZUElSbnovUT09"
            with urllib_request.urlopen(url_traditional) as response_traditional:
                data_traditional = json.load(response_traditional)

            time.sleep(0.3)
            # 搜尋簡體中文資料
            url_simplified = f"https://www.mxnzp.com/api/food_heat/food/search?keyword={encoded_keyword_simplified}&page={m}&app_id=uxnxyhgkujxpgqbt&app_secret=UHJqRjR6S25DaSttRWxZUElSbnovUT09"
            with urllib_request.urlopen(url_simplified) as response_simplified:
                data_simplified = json.load(response_simplified)

            if ('data' in data_traditional and 'list' in data_traditional['data']) or ('data' in data_simplified and 'list' in data_simplified['data']):
                for i in range(10):
                    if i < len(data_traditional['data']['list']):
                        # all(): 檢查迭代器中的所有元素是否都為真，當所有元素都為真時，函式會返回 True，否則返回 False，通常用於需要檢查多個條件的情況
                        if all(item['name'] != data_traditional['data']['list'][i]['name'] for item in search_results):
                            search_results.append(data_traditional['data']['list'][i])
                            messages.append(f"{len(search_results)}. {search_results[-1]['name']}")
                            if len(search_results) == 10:
                                break
                    if i < len(data_simplified['data']['list']):
                        traditional_name = s2t.convert(data_simplified['data']['list'][i]['name'])
                        if all(item['name'] != traditional_name for item in search_results):
                            data_simplified['data']['list'][i]['name'] = traditional_name
                            search_results.append(data_simplified['data']['list'][i])
                            messages.append(f"{len(search_results)}. {search_results[-1]['name']}")
                            if len(search_results) == 10:
                                break
        # 繁簡體相同
        else:
            url_traditional = f"https://www.mxnzp.com/api/food_heat/food/search?keyword={encoded_keyword_traditional}&page={m}&app_id=uxnxyhgkujxpgqbt&app_secret=UHJqRjR6S25DaSttRWxZUElSbnovUT09"
            with urllib_request.urlopen(url_traditional) as response_traditional:
                data_traditional = json.load(response_traditional)

            if 'data' in data_traditional and 'list' in data_traditional['data']:
                for i in range(10):
                    if i < len(data_traditional['data']['list']):
                        traditional_name = s2t.convert(data_traditional['data']['list'][i]['name'])
                        if all(item['name'] != traditional_name for item in search_results):
                            data_traditional['data']['list'][i]['name'] = traditional_name
                            search_results.append(data_traditional['data']['list'][i])
                            messages.append(f"{len(search_results)}. {search_results[-1]['name']}")
                            if len(search_results) == 10:
                                break
        if len(search_results) == 0:
            messages.append("目前還沒有相關的食物資料！！")
            break
        elif len(search_results) < 10:
            # 若 page = m 跑完 search_results 不滿 10 筆資料, 且兩種陣列有任一個是第一頁有十筆資料的，再跑下一頁 (m+=1)
            if ('data' in data_traditional and 'list' in data_traditional['data']) and i == len(data_traditional['data']['list']):
                m += 1
                time.sleep(0.3)
            elif ('data' in data_simplified and 'list' in data_simplified['data']) and i == len(data_simplified['data']['list']):
                m += 1
                time.sleep(0.3)
            else:
                break
        else:
            break
        
    return search_results, messages


#利用foodId, 獲取食物詳細資訊
def query(query_number,search_results):
    s2t = OpenCC('s2t')
    food_id = search_results[query_number - 1]['foodId']
    # print(food_id)
    
    time.sleep(0.3)
    base_url = "https://www.mxnzp.com/api/food_heat/food/details?foodId="
    url = base_url + parse.quote(food_id) + "&page=1&app_id=uxnxyhgkujxpgqbt&app_secret=UHJqRjR6S25DaSttRWxZUElSbnovUT09"

    with urllib_request.urlopen(url) as response:
        data = json.load(response)

    # 擷取筆資料的部分內容, 列印食物詳細資訊
    # name = data["data"]["name"]
    fftraditional_name = s2t.convert(data["data"]["name"])
    calory = data["data"]["calory"]
    calory_unit = data["data"]["caloryUnit"]
    protein = data["data"]["protein"]
    protein_unit = data["data"]["proteinUnit"]
    fat = data["data"]["fat"]
    fat_unit = data["data"]["fatUnit"]
    carbohydrate = data["data"]["carbohydrate"]
    carbohydrate_unit = data["data"]["carbohydrateUnit"]
    message = TextSendMessage(
        text=f"名稱： {fftraditional_name}\n熱量： {calory} {calory_unit}\n蛋白質： {protein} {protein_unit}\n脂質： {fat} {fat_unit}\n碳水化合物： {carbohydrate} {carbohydrate_unit}")
    
    
    return fftraditional_name , message


# 獲取Chrome驅動，訪問URL
def init_browser(img_keyword):
    url = f'https://www.google.com.hk/search?q={img_keyword}&tbm=isch'
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-infobars") # 禁用一些瀏覽器的信息欄
    service = Service(ChromeDriverManager().install())
    
    # 創建一個帶有特定配置的 Chrome 瀏覽器實例
    browser = webdriver.Chrome(service=service, options=chrome_options)
    
    browser.get(url)
    browser.maximize_window()
    
    return browser


def download_images_and_upload_to_github(round, img_keyword, github_repo,github_path, github_token):
    # Initialize the browser
    browser = init_browser(img_keyword)
    local_folder = 'imgs2'
    
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)
        
    data_url_count = 0
    max_image_size = 1024 * 1024
    
    
    for i in range(round):
        try:
            parent_element = WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.islrc')))
            
            img_elements = WebDriverWait(parent_element, 20).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'img')))
            
            for element in img_elements:
                img_url = element.get_attribute('src')
                
                img_attributes = element.get_attribute('outerHTML')
                
                if isinstance(img_url, str):
                    if img_url.startswith('data:image/jpeg'):
                        if 'data-sz' not in img_attributes:
                            if data_url_count == 0:
                                data_url_count += 1
                                continue
                            else:
                                img_data = re.search(r'base64,(.*)', img_url).group(1)
                                image_data = base64.b64decode(img_data)
                                
                                if len(image_data) < max_image_size:
                                    image = Image.open(BytesIO(image_data))
                                    image = image.convert("RGB")
                                    
                                    # Save the image locally
                                    filename = f'./{local_folder}/{img_keyword}.jpg'
                                    image.save(filename)
                                    break
                    else:
                        if len(img_url) <= 200:
                            if 'images' in img_url:
                                local_filename = f'./{local_folder}/{img_keyword}.jpg'
                                r = requests.get(img_url)
                                if len(r.content) < max_image_size:
                                    with open(local_filename, 'wb') as file:
                                        file.write(r.content)
                                        file.close()
                                        break
        except StaleElementReferenceException:
            print("出現StaleElementReferenceException錯誤，重新定位元素")
            continue
        
    time.sleep(0.5)
    browser.close()
    print("爬取完成") 
    return filename 

def upload_image_to_github(local_filename, github_repo, github_path, github_token):
    with open(local_filename, 'rb') as file:
        content = file.read()
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json",
    }
    url = f"https://api.github.com/repos/{github_repo}/contents/{github_path}"
    
    data = {
        "message": "Add image",
        "content": base64.b64encode(content).decode('utf-8'),
    }
    response = requests.put(url, headers=headers, json=data)
    content = response.json()
    
    image_url = content.get('download_url')
    img_message = ImageSendMessage(
    original_content_url=f'{image_url}',  
    preview_image_url=f'{image_url}'  
    )
    return img_message
    


# 主程式
if __name__ == '__main__':
    current_state = NORMAL
    keyword = ""
    
    app.run()


