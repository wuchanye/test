# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 07:39:16 2023

@author: harry
"""

from flask import Flask
app = Flask(__name__)


from flask import request, abort, render_template, jsonify
import os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import PostbackAction,ImageMessage,QuickReplyButton,MessageAction,QuickReply, MessageEvent, TextMessage, PostbackEvent, TextSendMessage, TemplateSendMessage, ConfirmTemplate, MessageTemplateAction, ButtonsTemplate, PostbackTemplateAction, URITemplateAction, CarouselTemplate, CarouselColumn, ImageCarouselTemplate, ImageCarouselColumn, FlexSendMessage,URIAction
import DB_Control as db
import Dimo_SearchFunction as Dimo_search
import rolltools_api_0717 as api
import Dimo_RichMenu_function as Rmenu
import Dimo_viewRecord as record
import Dimo_OCR as ocr
import time
import tempfile
from datetime import datetime, timedelta


line_bot_api = LineBotApi('nvO7flAlJDpYxX1wuW5dabRq/pFyRe3tf0tgCjIcXjCvURtfbNw4IquKOQzZaeLbOCwIUo9lZ/BdiQ6K1SZHyxSet6VCysh4X4cFDVGe67dilKFbRLP7JF5uL9Wk7Ei36Qy+0dHmR+IXZeKWbCFwjwdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('598e922f68d71936647ec0a88a20bde7')

db_using=db

filling_quantity={}
recorded_userInfo=[]
TEMP_IMAGE_DIRECTORY="./Ocr_temp/"

keyWordList=['是','否','確認紀錄','搜尋中，請稍待...','使用關鍵字查詢','目前正在操作頁面','目前正在問答頁面','觀看特定日期紀錄','觀看今天紀錄',"添加到我的紀錄","紀錄 1 份","紀錄 2 份","紀錄 3 份","紀錄 0.5 份"]

#LIFF靜態頁面
liffid_user = '1660781400-eP6OaxBn'
liffid_food = '1660781400-Pl4O8NRE'

@app.route('/userInfo')
def userInfo():
	return render_template('userinfo2.html', liffid = liffid_user)

@app.route('/foodInfo')
def foodInfo():
	return render_template('foodInfo2.html', liffid = liffid_food)

@app.route("/callback", methods=['POST'])
def callback():
     signature = request.headers['X-Line-Signature']
     body = request.get_data(as_text=True)
     try:
         handler.handle(body, signature)
     except InvalidSignatureError:
         abort(400)
     return 'OK'
 
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    mtext = event.message.text
    if mtext[:12]=='###我的基本資料###':
        record_userInfo(event,mtext,user_id)
    elif (db_using.check_user_in_userInfo(user_id)==False):
        recording_userInfo(event,user_id)      
    elif(db_using.check_user_in_userInfo(user_id)):
        if user_id in filling_quantity:
            recordWithCQ(event,mtext,user_id)
        elif mtext[:12]=='###食品營養資訊###':
            record_foodInfo(event, mtext, user_id)
        elif mtext in keyWordList :
            None
        else:
            Dimo_search.searching(event, mtext, user_id)
            
TEMP_IMAGE_DIRECTORY = "./Ocr_temp/"

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    # 取得使用者 ID
    user_id = event.source.user_id

    # 取得圖片訊息中的圖片 ID
    message_id = event.message.id

    # 获取用户发送的图像消息
    message_content = line_bot_api.get_message_content(message_id)

    try:
    # 创建临时目录，如果不存在
        os.makedirs(TEMP_IMAGE_DIRECTORY, exist_ok=True)
    
        # 创建临时文件，确保文件名唯一
        with tempfile.NamedTemporaryFile(dir=TEMP_IMAGE_DIRECTORY, delete=False, suffix='.png') as temp_file:
            # 写入图像数据到临时文件
            for chunk in message_content.iter_content():
                temp_file.write(chunk)
    
        # 获取临时文件的路径
        image_path = temp_file.name
        
        message = TextSendMessage(
                    text = "上傳圖片成功！\n請稍後辨識結果"
            )
        line_bot_api.reply_message(event.reply_token,message)
        
    
        print(image_path)
        image_path=image_path.replace("\\","/" )
        ocr.OCR(image_path,message_id)
    except Exception as e:        
        reply_message = "上傳圖片發生錯誤，请稍後再试。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
        print(str(e))
            
@handler.add(PostbackEvent) #PostbackTemplateAction 觸發此事件
def handle_postback(event):
    user_id = event.source.user_id
    postback_data = request.json['events'][0]['postback']['data']
    
    if postback_data=="choosed_date":
        selected_date = event.postback.params['date']
        view_specific_day_record(event,selected_date,user_id)
    else:   
        action,value=postback_data.split('^')
        if (db_using.check_user_in_userInfo(user_id)==False):
            recording_userInfo(event,user_id) 
        elif action=='CancleRecord':
            filling_quantity.pop(value)
            message = TextSendMessage(
                        text = '已取消'
                )
            line_bot_api.reply_message(event.reply_token,message)
        elif action=='addrecord':
                askingQuantity(event,value,user_id)
        elif action=='searchDetail':
            Dimo_search.queryTheDetail(event,value, user_id)
            # backdata = dict(parse_qsl(event.postback.data)) #取得 Postback 資料
            # if  backdata.get('action') == 'choose':
            #     sendBack_choose(event, backdata        
        elif action== 'ReRecrod':
            message = TextSendMessage(
                        text = '請輸入要記錄的份量數:'
                )
            line_bot_api.reply_message(event.reply_token,message)
        elif action=='recordWithQuantity':
            foodid,quantity=value.split(':')
            recordON(event, foodid, quantity, user_id)
        elif action=='richMenu':
            if value=='search':
                Rmenu.SearchFunction(event,user_id,line_bot_api,liffid_food)
            elif value=='document' : 
                Rmenu.How2Use(event,user_id,line_bot_api)
            elif value=='record' :
                Rmenu.RecordFunction(event,user_id,line_bot_api)
            elif value=='txtSearch':
                alert(event,user_id)
        elif action=='viewRecord':
            if value=='today':
                view_today_record(event,user_id)
            elif value=='chooseDate':
                chooseDate(event,user_id)
        elif action=='dlRecord':
            record_id,food_name,date=value.split(':')
            print(record_id,food_name,date)
            confirm_dlRecord(event,user_id,record_id,food_name,date)
        elif action == 'udRecord':
            None
        elif action == 'confirm':
            if value[:2]=="dl":
                temp=value[3:]
                print(temp)
                delete_data_call(event,temp,user_id)
     
def recording_userInfo(event,user_id):
    message = TemplateSendMessage(
            alt_text="填寫個人資料",
            template=ButtonsTemplate(
                title="請先填寫個人資料",
                text="點擊下面的按鈕開啟表單填寫",
                actions=[
                    URIAction(
                        label="填寫個人資料",
                        uri="https://liff.line.me/"+liffid_user
                    )
                ]
            )
        )
    recorded_userInfo.append(user_id)
    line_bot_api.reply_message(event.reply_token, message)
    
def record_foodInfo(event,mtext,user_id):
    data_string=mtext[13:]
    lines = data_string.split('\n')
    food_info = {}
    for line in lines:
         key, value = line.split(': ', 1)  # 使用冒號和空格分割
         if key=='熱量':
             value=value[:-3]
         elif key !='食品名稱' and key!='份量':
             value=value[:-2]
         food_info[key] = value
         
    success=db_using.record2dbWithCData(user_id, food_info)
    if success:
        message = TextSendMessage(
                    text = '記錄新增成功'
            )
        line_bot_api.reply_message(event.reply_token,message)
    else:
        message = TextSendMessage(
                    text = '發生錯誤'
            )
        line_bot_api.reply_message(event.reply_token,message)
        
def record_userInfo(event,mtext,user_id):
    data_string=mtext[13:]
    lines = data_string.split('\n')

    # 創建一個字典來存儲資訊
    user_info = {}
    for line in lines:
        key, value = line.split(': ', 1)  # 使用冒號和空格分割
        if key =='身高'or key=='體重':
            value=value[:-3]
        user_info[key] = value
    success=db_using.record_userInfo2Table(user_id, user_info)
    if success:
        message = TextSendMessage(
                    text = '基本資料寫入成功'
            )
        line_bot_api.reply_message(event.reply_token,message)
    else:
        message = TextSendMessage(
                    text = '發生錯誤'
            )
        line_bot_api.reply_message(event.reply_token,message)
        
def alert(event,user_id):
    try:
        message = TextSendMessage(
                    text = '請直接輸入要查詢的名稱'
            )
        line_bot_api.reply_message(event.reply_token,message)
    except:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤！'))

def view_today_record(event,user_id):
    result=db.queryfromDB("today", user_id)
    if (len(result)==0):
        message = TextSendMessage(
                    text = "您今天尚未創建任何紀錄!"
            )
        line_bot_api.reply_message(event.reply_token,message)
    else:
        # 創建最終的 JSON 物件
        flex_content=record.bubble_creat(len(result),result)
        message=FlexSendMessage(
                alt_text='紀錄',
                contents=flex_content
        )
        
        line_bot_api.reply_message(event.reply_token, message)

def view_specific_day_record(event,date,user_id):
    print(date)
    result=db.queryfromDB(date, user_id)
    if (len(result)==0):
        message = TextSendMessage(
                    text = "未取得任何紀錄!"
            )
        line_bot_api.reply_message(event.reply_token,message)
    elif result == 'noTable':
        message = TextSendMessage(
                    text = "未建立任何紀錄!"
            )
        line_bot_api.reply_message(event.reply_token,message)
    else:
        # 創建最終的 JSON 物件
        flex_content=record.bubble_creat(len(result),result)
        message=FlexSendMessage(
                alt_text='紀錄',
                contents=flex_content
        )
        
        line_bot_api.reply_message(event.reply_token, message)

def confirm_dlRecord(event,user_id,record_id,food_name,date):
    print(record_id)
    print(food_name)
    message = TemplateSendMessage(
            alt_text='移除紀錄確認',
            template=ConfirmTemplate(
                text='取消紀錄'+food_name+'?',
                actions=[
                    {
                        "type": "postback",
                        "label": "是",
                        "data": "confirm^dl:"+record_id+':'+food_name+':'+date,
                        'text': '是'
                        },
                      {
                        "type": "postback",
                        "label": "否",
                        "data":'cancel' ,
                        'text': '否'
                      }
                ]
            )
        )
    line_bot_api.reply_message(event.reply_token, message)

def delete_data_call(event,value,user_id):    
    itemId,foodName,date=value.split(':')
    print("Delete:"+foodName)
    success=db_using.deleteData(user_id, itemId, foodName, date)
    if success:
        message = TextSendMessage(
                    text = "刪除記錄成功"
            )
        line_bot_api.reply_message(event.reply_token,message)
    else:
        message = TextSendMessage(
                    text = "刪除記錄時發生錯誤!\n請再試一次!"
            )
        line_bot_api.reply_message(event.reply_token,message)
        
def chooseDate(event,user_id):
    # 獲取今天的日期
    today = datetime.now()
    
    
    # 計算一個月前和一個月後的日期
    one_month_ago = today - timedelta(days=30)
    one_month_ago = one_month_ago.strftime('%Y-%m-%d')
    one_month_later = today + timedelta(days=30)
    one_month_later = one_month_later.strftime('%Y-%m-%d')
    today=today.strftime('%Y-%m-%d')
    
    message = TemplateSendMessage(
            alt_text='請選擇日期',
            template=ButtonsTemplate(
                title='請選擇要查詢的日期',
                text='按下按鈕開啟日期選單',
                actions=[
                    {"type": "datetimepicker",
                      "label": "請選擇日期",
                      "data": "choosed_date",
                      "mode": "date",
                      "initial": today,
                      "max": one_month_later,
                      "min": one_month_ago
                      }
                ]
            )
        )
    
    line_bot_api.reply_message(event.reply_token, message)
    
def test(event,uid):
    try:
        message = TextSendMessage(
                    text = uid+'你好'
            )
        line_bot_api.reply_message(event.reply_token,message)
    except:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤！'))

def addQuantity(event,mtext, user_id):
    
    
    quantity,foodID=mtext[4:].split(':')
    
    success=db_using.updateQuantity(quantity, foodID,user_id)
    if success:
        message = TextSendMessage(
                    text = '記錄新增成功'
            )
        line_bot_api.reply_message(event.reply_token,message)
        
def askingQuantity(event,keyword,user_id):
    message = TextSendMessage(
               text = '請選擇要記錄的份量數',
               quick_reply=(QuickReply(
               items=[
                   QuickReplyButton(
                   action=PostbackAction(label="0.5份", data=f"recordWithQuantity^{keyword}:0.5",text='紀錄 0.5 份')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="1份", data=f"recordWithQuantity^{keyword}:1",text='紀錄 1 份')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="2份", data=f"recordWithQuantity^{keyword}:2",text='紀錄 2 份')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="3份", data=f"recordWithQuantity^{keyword}:3",text='紀錄 3 份')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="自訂份量", data=f"recordWithQuantity^{keyword}:other")
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="取消輸入",data=f'CancleRecord^{user_id}')
                       )
                   ]
               )
           )
        )       
    line_bot_api.reply_message(event.reply_token,message)
    # time.sleep(2)
    filling_quantity[user_id]={
        'foodid':keyword
        }

def recordON(event,foodID, quantity,user_id):
    if quantity=='other':
        message = TextSendMessage(
                    text = '請輸入自訂份量數字:',
                    quick_reply=(QuickReply(
                    items=[
                        QuickReplyButton(
                        action=PostbackAction(label="取消輸入",data=f'CancleRecord^{user_id}')
                                    )
                        ]
                    )
                )
            )
        line_bot_api.reply_message(event.reply_token,message)
    else:
        success=db_using.record2db(quantity,foodID, user_id)
        if success:
            message = TextSendMessage(
                        text = '記錄新增成功'
                )
            if filling_quantity[user_id]:    
                filling_quantity.pop(user_id)
            line_bot_api.reply_message(event.reply_token,message)
        
def recordWithCQ(event,keyword,user_id):
    food_id=filling_quantity[user_id].get('foodid')
    if(keyword in ["添加到我的紀錄","紀錄 1 份","紀錄 2 份","紀錄 3 份","紀錄 0.5 份"]):
        None
    elif(keyword=='確認紀錄'):
        
        filling_quantity.pop(user_id)
    elif (keyword.isdigit()==False):
        message = TextSendMessage(
                    text = '請輸入數字',
                    quick_reply=(QuickReply(
                    items=[
                        QuickReplyButton(
                        action=PostbackAction(label="取消輸入",data=f'CancleRecord^{user_id}')
                                    )
                        ]
                    )
                )
                    
            )
        line_bot_api.reply_message(event.reply_token,message)
    elif keyword.isnumeric() or (keyword.count('.') == 1 and keyword.replace('.', '').isnumeric()):
        value = float(keyword)
        if value <= 0:
            message = TextSendMessage(
                        text = '請輸入正數',
                        quick_reply=(QuickReply(
                        items=[
                            QuickReplyButton(
                            action=PostbackAction(label="取消輸入",data=f'CancleRecord^{user_id}')
                                        )
                            ]
                        )
                    )
                )
            line_bot_api.reply_message(event.reply_token,message)
        elif value >= 20:
            message = TextSendMessage(
                        text = '您輸入的數似乎過大，請確認是否重新輸入',
                        quick_reply=(QuickReply(
                        items=[
                            QuickReplyButton(
                            action=PostbackAction(label="是",data='ReRecrod^{keyword}')
                                        ),
                            QuickReplyButton(
                            action=PostbackAction(label="否",data=f"recordWithQuantity^{food_id}:{value}",text='確認紀錄')
                                        )
                            ]
                        )
                )
            )
            line_bot_api.reply_message(event.reply_token,message)
        else:
            message = TextSendMessage(
                        text = f'紀錄 {value} 份?',
                        quick_reply=(QuickReply(
                        items=[
                            QuickReplyButton(
                            action=PostbackAction(label="確認",data=f'recordWithQuantity^{food_id}:{value}',text='確認紀錄')
                                        ),
                            QuickReplyButton(
                            action=PostbackAction(label="重新輸入",data='ReRecrod^{keyword}')
                                        ),
                            QuickReplyButton(
                            action=PostbackAction(label="取消",data=f"CancleRecord^{user_id}")
                                        )
                            ]
                        )
                    )
                )
            line_bot_api.reply_message(event.reply_token,message)
        return True, value
    return False, None

if __name__ == '__main__':
    app.run()