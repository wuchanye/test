from opencc import OpenCC
import urllib.request as request
import urllib.parse as parse
import os
import requests
import base64
import json
import time
from bs4 import BeautifulSoup
import hashlib

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
    image_content=download_images_with_beautifulsoup(1, name)
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
    # print('IMAGE_PATH='+str(img))
    github_token = os.getenv('github_token')
    data={'name':name,'calory':calory,'protein':protein,'fat':fat,'carb':carbohydrate}
    dataAndunit={'name':name,'calory':calory+' '+ calory_unit,'protein':protein+' '+protein_unit,'fat':fat+' '+fat_unit,'carb':carbohydrate+' '+carbohydrate_unit}
    if unit==True and picON==True:
        image_url=upload_image_to_github(image_content, name, github_token)
        return dataAndunit,image_url
    elif unit==True and picON==False:
        return dataAndunit
    else:
        return data
    
def download_images_with_beautifulsoup(round, img_keyword):
    # 獲取 html 內容
    url = f'https://www.google.com.hk/search?q={img_keyword}&tbm=isch'
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')

    data_url_count = 0
    max_image_size = 1024 * 1024
    img_content = None  # 用于存储图像内容
    
    for i in range(round):
        try:
            # 分析網頁, 找圖片元素
            img_elements = soup.find_all('img') 
            
            for element in img_elements:
                # 遍歷元素, 鎖定屬性
                img_url = element.get('src')
                if isinstance(img_url, str) and img_url.startswith('https://'): # 留下https://開頭的url
                    if data_url_count == 0:
                        data_url_count += 1
                        continue
                    else:
                        r = requests.get(img_url)
                        if len(r.content) < max_image_size: 
                            img_content = r.content # 將二進制內容儲存在參數
                            break
        except Exception as e:
            print(f"出现错误：{str(e)}")
            continue
        
    print("爬取完成")
    time.sleep(0.5)
    return img_content

def upload_image_to_github(image_content, keyword, github_token):
    github_username = 'wuchanye'
    github_repo = 'test'
    github_folder = 'imgs4food'
    filename = keyword + '.jpg'
    img_message = None
    
    
    sha1 = hashlib.sha1()
    sha1.update(image_content)
    sha1_hash = sha1.hexdigest()
    
    url = f'https://api.github.com/repos/{github_username}/{github_repo}/contents/{github_folder}/{filename}'
    headers = {
        'Authorization': f'Bearer {github_token}',
    }
    
    response = requests.get(url, headers=headers)
    existing_file_data = response.json()
    existing_sha = existing_file_data.get('sha', '')
    
    if existing_sha != sha1_hash:
        
        headers = {
            'Authorization': f'Bearer {github_token}',
            'Content-Type': 'application/json',
        }

        data = {
            'message': 'Update image',
            'content': base64.b64encode(image_content).decode('utf-8'),
            'sha': existing_sha,
        }

        response = requests.put(url, headers=headers, json=data)

        if response.status_code == 200 or response.status_code == 201:
            image_url = response.json().get('content').get('download_url')
            #img_message = ImageSendMessage(
            #    original_content_url=image_url,
            #    preview_image_url=image_url
            #)
            print("文件已成功更新到GitHub存储库的文件夹。")
        else:
            print(f"上传文件失败，HTTP响应代码: {response.status_code}")
            print(f"响应内容: {response.text}")
            #img_message = TextSendMessage(text="上傳圖片失敗。")
    return image_url
    

if(__name__)=="__main__":
    keyword = input("請輸入食物名稱：")
    search_results = search(keyword)
    #print(search_results) # 測試用
    
    if search_results != []: # 不是None唷!
        query_number = int(input("\n請選擇想查詢的食物代號：")) #先利用query number代替點選的步驟
        query(query_number, search_results)
    
