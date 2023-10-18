from opencc import OpenCC
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from io import BytesIO
from PIL import Image
import pyimgur
import urllib.request as request
import urllib.parse as parse

import os
import requests
import re
import base64
import json
import time

# app_id=uxnxyhgkujxpgqbt&app_secret=UHJqRjR6S25DaSttRWxZUElSbnovUT09

#搜尋食物 獲取食物名稱,foodId -NEW
def search(appid,secret,name):
    encoded_keyword_traditional = parse.quote(name)  # 繁體中文關鍵字
    t2s = OpenCC('t2s') #繁轉簡
    s2t = OpenCC('s2t') #簡轉繁
    simplified_name = t2s.convert(name)
    encoded_keyword_simplified = parse.quote(simplified_name)  # 簡體中文關鍵字
    
    data_simplified = {} #解決繁簡相同時 未賦予值的問題
    c_list = []
    count = 0
    m = 1
    while True:
        # 繁簡相異
        if encoded_keyword_traditional!=encoded_keyword_simplified:
            
            # 搜尋繁體中文資料
            url_traditional = f"https://www.mxnzp.com/api/food_heat/food/search?keyword={encoded_keyword_traditional}&page={m}&"+"app_id={}&app_secret={}".format(appid,secret)
            with request.urlopen(url_traditional) as response_traditional:
                data_traditional = json.load(response_traditional) 
            
            time.sleep(1) #訪問間隔
            # 搜尋簡體中文資料
            url_simplified = f"https://www.mxnzp.com/api/food_heat/food/search?keyword={encoded_keyword_simplified}&page={m}&"+"app_id={}&app_secret={}".format(appid,secret)
            with request.urlopen(url_simplified) as response_simplified:
                data_simplified = json.load(response_simplified) 
                
            
            if ('data' in data_traditional and 'list' in data_traditional['data']) or ('data' in data_simplified and 'list' in data_simplified['data']):
                for i in range(10):
                    # len(): 解決陣列沒有元素的情況
                    if i < len(data_traditional['data']['list']):
                        # all(): 檢查迭代器中的所有元素是否都為真，當所有元素都為真時，函式會返回 True，否則返回 False，通常用於需要檢查多個條件的情況
                        if all(item['name'] != data_traditional['data']['list'][i]['name'] for item in c_list):
                            c_list.append(data_traditional['data']['list'][i]) 
                            print(f"{count+1}. {c_list[count]['name']}")
                            count+=1
                            if count ==10:
                                break
                    if i < len(data_simplified['data']['list']):
                        traditional_name = s2t.convert(data_simplified['data']['list'][i]['name'])
                        if all(item['name'] != traditional_name for item in c_list):
                            data_simplified['data']['list'][i]['name'] = traditional_name
                            c_list.append(data_simplified['data']['list'][i])
                            print(f"{count+1}. {c_list[count]['name']}")
                            count+=1
                            if count == 10:
                                break
        # 繁簡體相同
        else: 
            url_traditional = f"https://www.mxnzp.com/api/food_heat/food/search?keyword={encoded_keyword_traditional}&"+"app_id={}&app_secret={}".format(appid,secret)
            with request.urlopen(url_traditional) as response_traditional:
                data_traditional = json.load(response_traditional)
            
            if 'data' in data_traditional and 'list' in data_traditional['data']:
                for i in range(10):
                    if i < len(data_traditional['data']['list']):
                        traditional_name = s2t.convert(data_traditional['data']['list'][i]['name'])
                        if all(item['name'] != traditional_name for item in c_list):
                            data_traditional['data']['list'][i]['name'] = traditional_name
                            c_list.append(data_traditional['data']['list'][i]) 
                            print(f"{count+1}. {c_list[count]['name']}")
                            count+=1
                            if count ==10:
                                break
        if count == 0:
            print("目前還沒有相關的食物資料！！")
            return None
            break
        elif count != 10:
            # while True - 若 page = m 跑完 c_list 不滿 10 筆資料而且兩種陣列有任一個是第一頁有十筆資料的，再跑下一頁 (m+=1)
            if ('data' in data_traditional and 'list' in data_traditional['data']) and i == len(data_traditional['data']['list']):
                m += 1
                time.sleep(1)  # 訪問間隔
            elif ('data' in data_simplified and 'list' in data_simplified['data']) and i == len(data_simplified['data']['list']):
                m += 1
                time.sleep(1)  # 訪問間隔
            else:
                break
        else:
            break
            
    return c_list



#利用foodId, 獲取食物詳細資訊, 經選擇的那筆資料為food_data 
def query(appid,secret,food_id,unit,picON):
    
    s2t = OpenCC('s2t')
    
    #print(food_id)
    time.sleep(1) #訪問間隔

    base_url = "https://www.mxnzp.com/api/food_heat/food/details?foodId="
    url = base_url + parse.quote(food_id) + "&page=1&app_id={}&app_secret={}".format(appid,secret)
    
    with request.urlopen(url) as response:
        data = json.load(response)

    # 擷取其中一筆資料的部分內容, 列印食物詳細資訊
    #name = data["data"]["name"]
    name = s2t.convert(data["data"]["name"])
    img=download_images(1, name)
    time.sleep(1) #訪問間隔
    calory = data["data"]["calory"]
    calory_unit = data["data"]["caloryUnit"]
    protein = data["data"]["protein"]
    protein_unit = data["data"]["proteinUnit"]
    fat = data["data"]["fat"]
    fat_unit = data["data"]["fatUnit"]
    carbohydrate = data["data"]["carbohydrate"]
    carbohydrate_unit = data["data"]["carbohydrateUnit"]
    print("名稱：",name,"\n熱量：",calory,calory_unit,"\n蛋白質：",protein,protein_unit,"\n脂質：",fat,fat_unit,"\n碳水化合物：",carbohydrate,carbohydrate_unit)
    print('IMAGE_PATH='+str(img))
    imgUrl=upload_to_imgur(img)
    data={'name':name,'calory':calory,'protein':protein,'fat':fat,'carb':carbohydrate}
    dataAndunit={'name':name,'calory':calory+' '+ calory_unit,'protein':protein+' '+protein_unit,'fat':fat+' '+fat_unit,'carb':carbohydrate+' '+carbohydrate_unit}
    if unit==True and picON==True:
        return dataAndunit,imgUrl
    elif unit==True and picON==False:
        return dataAndunit
    else:
        return data
    
# 獲取Chrome驅動，訪問URL
def init_browser(img_keyword):
    url = f'https://www.google.com.hk/search?q={img_keyword}&tbm=isch'
    
    chrome_options = webdriver.ChromeOptions()
    
    chrome_options.add_argument("--disable-infobars") # 禁用一些瀏覽器的信息欄
    chrome_options.add_argument("--headless")
    
    # 創建一個帶有特定配置的 Chrome 瀏覽器實例
    chromedriver_path = "D:\\LineBotWithPython\\DIMO\\DIMO3.0\\chromedriver-win64\\chromedriver.exe"
    browser = webdriver.Chrome(executable_path=chromedriver_path,options=chrome_options)
    
    browser.get(url)
    browser.maximize_window()
    
    return browser


# 下載圖片
def download_images(round, img_keyword):
    
    existing_image_path = check_existing_images(img_keyword)
    if existing_image_path:
        print(f"使用現有圖片：{existing_image_path}")
        return existing_image_path
    else:
        browser = init_browser(img_keyword)
        local_folder = 'imgs4food'
        
        if not os.path.exists(local_folder): # 資料夾不存在時創建一個
            os.makedirs(local_folder)
            
        # img_url_dic = [] # 記錄下載過的圖片地址，避免重複下載
        # count = 0  # 圖片序號
        data_url_count = 0  # 計數 Data URL 圖片數量
        max_image_size = 1024 * 1024  # 目前圖片限制大小為 1 MB
        
        for i in range(round):
            try:
                # 分析網頁,找到圖片元素
                parent_element = WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.islrc')))
                
                img_elements = WebDriverWait(parent_element, 20).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, 'img')))
                
                # 遍歷元素 鎖定需要的屬性
                for element in img_elements:
                    img_url = element.get_attribute('src')
                    
                    img_attributes = element.get_attribute('outerHTML') # 獲取 img 標籤中的"所有"屬性
                    
                    # 確保'img_url'是一個字符串，排除 get_attribute('src') 返回 None 或其他非字符串值的問題。
                    if isinstance(img_url, str):
                        
                        # 判斷是否是 Data URL
                        if img_url.startswith('data:image/jpeg'): 
                            if 'data-sz' not in img_attributes:  # 避免下載到網站小圖標
                                if data_url_count == 0: # 跳過第一張
                                    data_url_count += 1
                                    continue  # 經過試驗 第二張好於第一張
                                else:
                                    img_data = re.search(r'base64,(.*)', img_url).group(1) # 提取 Data URL 中的圖片數據, 利用正則表達式捕獲base64,後面的全部
                                    image_data = base64.b64decode(img_data)  # 解碼圖片數據成二進制數據
                                    
                                    if len(image_data) < max_image_size:
                                        image = Image.open(BytesIO(image_data)) # 將圖片數據轉換為圖片對象
                                        image = image.convert("RGB") # 將圖片轉換為 RGB 模式
                                        
                                        # 下載並保存圖片到當前目錄下
                                        #filename = f'./imgs/{img_keyword}_{str(count)}.jpg'
                                        filename = f'./imgs4food/{img_keyword}.jpg'
                                        image.save(filename)
                                        break
                                        #count += 1
                                        #print('this is ' + str(count) + 'st img')
                                        # time.sleep(0.2) # 防止反爬機制
                        else:
                            
                            if len(img_url) <= 200: # URL太長基本上就不是圖片的URL，先過濾掉，爬後面的
                                
                                # 判斷是否是普通的 PNG 圖檔
                                if 'images' in img_url: 
                                    
                                    # 下載並保存圖片到當前目錄下
                                    #filename = f'./imgs/{img_keyword}_{str(count)}.jpg'
                                    filename = f'./imgs4food/{img_keyword}.jpg'
                                    r = requests.get(img_url)
                                    if len(r.content) < max_image_size:
                                        with open(filename, 'wb') as file:
                                            file.write(r.content)
                                            file.close()
                                            break
                                            #count += 1
                                            #print('this is ' + str(count) + 'st img')
                                            # time.sleep(0.2) # 防止反爬機制
                                
            except StaleElementReferenceException:
                print("出現StaleElementReferenceException錯誤，重新定位元素")
                continue
            
        time.sleep(0.5)
        browser.close()
        print("爬取完成")
        
        return filename
    
def check_existing_images(img_keyword):
    local_folder = 'imgs4food'

    if not os.path.exists(local_folder):  # 資料夾不存在時，表示沒有相同關鍵字的圖片
        return None

    # 取得資料夾中所有的檔案名稱
    existing_images = os.listdir(local_folder)

    # 檢查是否有以 img_keyword 為名的圖片
    for filename in existing_images:
        if f'{img_keyword}.jpg' in filename:
            return os.path.join(local_folder, filename)  # 返回已存在的圖片的完整路徑

    # 如果沒有相同關鍵字的圖片，返回 None
    return None

# 上傳圖片 並取得url
def upload_to_imgur(img_path):
    
    # Imgur API 密鑰
    client_id = "1c126fdbf51fd36"
    # client_secret = "e923e678d27d8f019913f26511a4d02d060899ba"
    title = "Uploaded with PyImgur"
    
    im = pyimgur.Imgur(client_id)
    # 上傳圖片並獲取圖片的 URL
    uploaded_image = im.upload_image(img_path, title=title)
    image_url = uploaded_image.link
    
    # img_message = ImageSendMessage(
    #     original_content_url=f'{image_url}',  
    #     preview_image_url=f'{image_url}'  
    # )
    return image_url

if(__name__)=="__main__":
    keyword = input("請輸入食物名稱：")
    search_results = search(keyword)
    #print(search_results) # 測試用
    
    if search_results != []: # 不是None唷!
        query_number = int(input("\n請選擇想查詢的食物代號：")) #先利用query number代替點選的步驟
        query(query_number, search_results)
    