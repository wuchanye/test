import cv2
from google.cloud import vision_v1
import io

def OCR(img_path,img_id):
    print(img_path)
    print(img_id)
    new_size = (800, 800)
    # 讀取並重新調整圖片大小
    original_image = cv2.imread(img_path)
    resized_image = resize_image(original_image, new_size)

    # 尋找主要方框並繪製
    result_image, main_box = find_main_nutrition_box(resized_image)

    # 裁切方框內的影像
    if main_box is not None:
        x, y, w, h = cv2.boundingRect(main_box)
        cropped_image = resized_image[y:y+h, x:x+w]

        # 保存裁剪後的圖像
        cv2.imwrite(f'./Ocr_temp/Nutrition_Label_{img_id}.jpg', cropped_image)

        # 使用 Google Cloud Vision API 提取文本
        credentials_path = 'mindful-marking-400311-b4645f955373.json'  # 自己路徑的Json檔名
        extracted_text = extract_text_from_image(f'./Ocr_temp/Nutrition_Label_{img_id}.jpg', credentials_path)

        # 將提取的文本整理成字典
        extracted_text_dict = {'text': extracted_text}

        # 顯示提取的文本
        print(extracted_text_dict)
    else:
        print('未找到主要方框，無法識別文字。')

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

def extract_text_from_image(image_path, credentials_path):
    # 使用認證憑據文件創建Vision API客户端
    client = vision_v1.ImageAnnotatorClient.from_service_account_file(credentials_path)

    # 讀取圖片文件
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    # 創建圖片對象
    image = vision_v1.Image(content=content)

    # 使用文本檢测功能識别圖片中的文字
    response = client.text_detection(image=image)
    texts = response.text_annotations

    extracted_text = []
    if texts:
        for text in texts:
            extracted_text.append(text.description)
    return extracted_text

if __name__ == '__main__':
    # 圖片文件路径
    image_path = 'food_packaging18.jpg'
    new_size = (800, 800)
    # 讀取並重新調整圖片大小
    original_image = cv2.imread(image_path)
    resized_image = resize_image(original_image, new_size)

    # 尋找主要方框並繪製
    result_image, main_box = find_main_nutrition_box(resized_image)

    # 裁切方框內的影像
    if main_box is not None:
        x, y, w, h = cv2.boundingRect(main_box)
        cropped_image = resized_image[y:y+h, x:x+w]

        # 保存裁剪後的圖像
        cv2.imwrite('Cropped_Nutrition_Label.jpg', cropped_image)

        # 使用 Google Cloud Vision API 提取文本
        credentials_path = 'ocr-test-400305-7bc7fdca3379.json'  # 自己路徑的Json檔名
        extracted_text = extract_text_from_image('Cropped_Nutrition_Label.jpg', credentials_path)

        # 將提取的文本整理成字典
        extracted_text_dict = {'text': extracted_text}

        # 顯示提取的文本
        print(extracted_text_dict)
    else:
        print('未找到主要方框，無法識別文字。')
