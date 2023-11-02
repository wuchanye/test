import cv2
from google.cloud import vision_v1
import requests
import base64
import numpy as np
import re


def OCR(image_data,img_id):
    # 讀取並重新調整圖片大小
    new_size = (800, 800)
    
    # 将二进制数据转换为 NumPy 数组
    image_array = np.frombuffer(image_data, np.uint8)
    # 使用 OpenCV 读取图像
    original_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    resized_image = resize_image(original_image, new_size)

    # 尋找主要方框並繪製
    result_image, main_box = find_main_nutrition_box(resized_image)

    # 裁切方框內的影像
    if main_box is not None:
        x, y, w, h = cv2.boundingRect(main_box)
        cropped_image = resized_image[y:y+h, x:x+w]
        
        # 将图像转换为二进制数据
        success, image_data = cv2.imencode('.jpg', cropped_image)
        if success:
            try:
                image_content = image_data.tobytes()
                # upload_image_to_github(image_content, img_id)

                # 使用 Google Cloud Vision API 提取文本
                credentials_path = '/etc/secrets/google_application_credentials'   # Json憑證的路徑>>上render需設置secret file, 不從本機獲取
                extracted_text = extract_text_from_image(image_content, credentials_path)
                ocr_result=trans2dict(extracted_text[0])
                return ocr_result
            except IndexError:
                return 'no boxes'
    else:
        print('未找到主要方框，無法識別文字。')
        return 'no boxes'

def resize_image(image, new_size):
    return cv2.resize(image, new_size)

def find_main_nutrition_box(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, threshold1=30, threshold2=100)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    main_box = None
    max_area = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
            main_box = contour

    if main_box is not None:
        epsilon = 0.05 * cv2.arcLength(main_box, True)
        approx = cv2.approxPolyDP(main_box, epsilon, True)
        cv2.drawContours(image, [approx], 0, (0, 255, 0), 2)

    return image, main_box

def extract_text_from_image(image_content, credentials_path):
    # 使用認證憑據文件創建Vision API客户端
    client = vision_v1.ImageAnnotatorClient.from_service_account_file(credentials_path)

    # 創建圖片對象
    image = vision_v1.Image(content=image_content)

    # 使用文本檢测功能識别圖片中的文字
    response = client.text_detection(image=image)
    texts = response.text_annotations

    extracted_text = []
    if texts:
        for text in texts:
            extracted_text.append(text.description)
    return extracted_text

def upload_image_to_github(image_content, img_id):
    # print(image_content)
    github_username = 'wuchanye'
    github_repo = 'test'
    github_folder = 'Ocr_temp'
    github_token = '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'
    filename = img_id + '.jpg'
    current_sha = None
    
    # with open('saved_image.jpg', 'wb') as file:
    #     file.write(image_content)
    
    url = f'https://api.github.com/repos/{github_username}/{github_repo}/contents/{github_folder}/{filename}'
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()
        if 'sha' in content:
            current_sha = content['sha']
    
    
    
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Content-Type': 'application/json',
    }
    

    data = {
        'message': 'Update image',
        'content': base64.b64encode(image_content).decode('utf-8'),
        'sha': current_sha
    }

    response = requests.put(url, headers=headers, json=data)
    print(response.status_code)

    if response.status_code == 200 or response.status_code ==201:
        print("文件已成功更新到GitHub存储库的文件夹。")
        # image_url = response.json().get('content').get('download_url')
        # print(img_id)
    else:
        print(f"上传文件失败，HTTP响应代码: {response.status_code}")
        print(f"响应内容: {response.text}")

def trans2dict(exText):
    try:
        text=exText
        print(text)
        food_info={}
    
        list_text=text.split('\n')
        
        index_1 = next((i for i, item in enumerate(list_text) if item.startswith("每一份量") ), None)
        index_2 = next((i for i, item in enumerate(list_text) if item.startswith("本包裝含") and item.endswith("份")), None)
    
        if index_1 is not None and index_2 is not None :
            per_serving = re.search(r'(\d+)[\s]*(\w+)', list_text[index_1]).group()
            package_serving = re.search(r'(\d+)', list_text[index_2]).group()
            # print(f"每一份量的數值: {per_serving} 公克")
            # print(f"本包裝含的份量數: {package_serving} 份")
            food_info['每一份量']=per_serving
            food_info['包裝份量'] = package_serving
            if index_1< index_2:
                list_text.pop(index_2)
                list_text.pop(index_1-1)
            else:
                list_text.pop(index_1)
                list_text.pop(index_2-1)
        else:
            print("格式不正確")
            return 'non support'
            
        index_per_serving = list_text.index('每份')
    
        sublist_per_serving = list_text[index_per_serving:index_per_serving + 9]
    
        calories_value = re.search(r'\d+', sublist_per_serving[0+1]).group()
        protein_value = re.search(r'\d+(\.\d+)?', sublist_per_serving[1+1]).group()
        fat_value = re.search(r'\d+(\.\d+)?', sublist_per_serving[2+1]).group()
        carb_value = re.search(r'\d+(\.\d+)?', sublist_per_serving[5+1]).group()
    
        food_info['熱量']=calories_value
        food_info['蛋白質']=protein_value
        food_info['脂肪']=fat_value
        food_info['碳水化合物']=carb_value
    
        print(food_info)
        return food_info
    except ValueError:
        return 'non support'
