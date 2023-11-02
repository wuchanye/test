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
import DimoGPT as chat

line_bot_api = LineBotApi(os.environ.get('line_channel_token'))
handler = WebhookHandler(os.environ.get('line_secret'))

db_using=db

filling_quantity={}
udQuantity={}
recorded_userInfo=[]
chatMode={}

keyWordList=['是','否','確認紀錄','確認修改','搜尋中，請稍待...','使用關鍵字查詢','目前正在操作頁面','目前正在問答頁面','觀看特定日期紀錄','觀看今天紀錄',"添加到我的紀錄","紀錄 1 份","紀錄 2 份","紀錄 3 份","紀錄 0.5 份"]
#LIFF靜態頁面
liffid_user = os.environ.get('liffid_user')
liffid_food = os.environ.get('liffid_food')
liffid_viewUserInfo= os.environ.get('liffid_viewUserInfo')
user_defalt_info={}
hist=[]
filling_imgInfo={}

@app.route('/userInfo')
def userInfo():
	return render_template('userinfo2.html', liffid = liffid_user)

@app.route('/foodInfo')
def foodInfo():
	return render_template('foodInfo2.html', liffid = liffid_food)

@app.route('/getUserId')
def getUserId():
   return render_template('getUserID.html', liffid=liffid_viewUserInfo)

@app.route('/viewUserInfo', methods=['GET','POST'])
def viewUserInfo():
    if request.method == 'POST':
        user_id = request.values['userID']
        print(user_id)
        global user_defalt_info
        defaltInfo = db_using.view_user_info(user_id)

        user_defalt_info = {}
        user_defalt_info['gender'] = defaltInfo[2]
        user_defalt_info['height'] = defaltInfo[3]
        user_defalt_info['weight'] = defaltInfo[4]
        user_defalt_info['exerciseIntensity'] = defaltInfo[5]
        user_defalt_info['fitnessGoal'] = defaltInfo[6]
        print(user_defalt_info)
        return render_template('viewUserInfo.html', liffid = liffid_viewUserInfo,user_info=user_defalt_info)
    else:
        return render_template('viewUserInfo.html', liffid = liffid_viewUserInfo,user_info=user_defalt_info)
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
        if user_id in filling_quantity :
            recordWithCQ(event,mtext,user_id)
        elif  user_id in udQuantity:
            updateWithCQ(event,mtext,user_id)
        elif user_id in filling_imgInfo :
            recordImgData(event,user_id,mtext)
        elif mtext[:12]=='###食品營養資訊###':
            record_foodInfo(event, mtext, user_id)
        elif mtext in keyWordList :
            None
        elif user_id not in chatMode:
            Dimo_search.searching(event, mtext, user_id)
        elif user_id in chatMode: 
            if chatMode[user_id].get('mode')=='systemUse':
                Dimo_search.searching(event, mtext, user_id)
            elif chatMode[user_id].get('mode')=='chat':
                loading2GPT(event,mtext,user_id)
                
        else:
            
            message = TextSendMessage(
                        text = '預設操作模式\n直接輸入關鍵字可進行查詢，\n或點擊選單切換模式或使用功能。',
                        quick_reply=(QuickReply(
                        items=[
                            {
                              "type": "action",
                              "action": {
                                "type": "postback",
                                "label": "開啟圖文選單",
                                "data":'None',
                                'inputOption':'openRichMenu'
                              }
                            }
                    ]
                    )
                )
             )
            line_bot_api.reply_message(event.reply_token,message)

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    # 取得使用者 ID
    user_id = event.source.user_id
    # try:
        # 取得圖片訊息中的圖片 ID
    message_id = event.message.id
    
    # 获取用户发送的图像消息
    message_content = line_bot_api.get_message_content(message_id)
    image_data = message_content.content
    result=ocr.OCR(image_data,message_id)
    
    if result=='non support':
        message = TextSendMessage(
                    text = '很抱歉，此格式尚不支援辨識',
                    quick_reply=(QuickReply(
                    items=[
                            {
                              "type": "action",
                              "action": {
                                "type": "uri",
                                "label": "手動輸入資訊",
                                "uri": "https://liff.line.me/"+liffid_food
                              }
                            }
                        ]
                    )
                )
            )
        line_bot_api.reply_message(event.reply_token,message)
    elif result=='no boxes':
        message = TextSendMessage(
                    text = '未找到營養標籤\n請確認上傳圖片正確性\n或上傳更清晰之圖像'
            )
        line_bot_api.reply_message(event.reply_token,message)
    else:
        showImgResult(event, user_id, result)
            
@handler.add(PostbackEvent) #PostbackTemplateAction 觸發此事件
def handle_postback(event):
    user_id = event.source.user_id
    postback_data = request.json['events'][0]['postback']['data']
    if postback_data=='None':
        None
    elif postback_data=="choosed_date":
        selected_date = event.postback.params['date']
        view_specific_day_record(event,selected_date,user_id)
    elif postback_data=='change-to-systemMode' :
        chatMode[user_id]={'mode':'systemUse','data':None}
        message = TextSendMessage(
                    text = '已切換至操作模式'
            )
        line_bot_api.reply_message(event.reply_token,message)
    elif postback_data=='systemMode':
        chatMode[user_id]={'mode':'systemUse','data':None}
        # message = TextSendMessage(
        #             text = '現在是操作模式，mode='+chatMode[user_id].get('mode')
        #     )
        # line_bot_api.reply_message(event.reply_token,message)
    elif postback_data=='change-to-chatMode' :
        chatMode[user_id]={'mode':'chat','data':hist}
        message = TextSendMessage(
                    text = '已切換至智能問答模式'
            )
        line_bot_api.reply_message(event.reply_token,message)
    elif postback_data=='chatMode':
        chatMode[user_id]={'mode':'chat','data':hist}
        # message = TextSendMessage(
        #             text = '現在是智能問答模式，mode='+chatMode[user_id].get('mode')
        #     )
        # line_bot_api.reply_message(event.reply_token,message)
        
    else:   
        action,value=postback_data.split('^')
        if (db_using.check_user_in_userInfo(user_id)==False):
            recording_userInfo(event,user_id) 
        elif action=='CancleRecord':
            if user_id in filling_quantity:
                filling_quantity.pop(value)
            message = TextSendMessage(
                        text = '已取消'
                )
            line_bot_api.reply_message(event.reply_token,message)
        elif action=='CancleUpdate':
            if user_id in udQuantity:
                udQuantity.pop(value)
            message = TextSendMessage(
                        text = '已取消'
                )
            line_bot_api.reply_message(event.reply_token,message)
        elif action=='addrecord':
            food_id,name=value.split(':')
            askingQuantity(event,food_id,name,user_id)
        elif action=='searchDetail':
            Dimo_search.queryTheDetail(event,value, user_id)
            # backdata = dict(parse_qsl(event.postback.data)) #取得 Postback 資料
            # if  backdata.get('action') == 'choose':
            #     sendBack_choose(event, backdata     
        elif action=='Update':
            id,name,quantity,date=value.split(':')
            success=db_using.updateQuantity(quantity, id, user_id, name, date)
            if success:
                message = TextSendMessage(
                            text = '修改成功'
                    )
                line_bot_api.reply_message(event.reply_token,message)
                if user_id in udQuantity:
                    udQuantity.pop(user_id)
        elif action== 'ReRecrod':
            message = TextSendMessage(
                        text = '請輸入要記錄的份量數:'
                )
            line_bot_api.reply_message(event.reply_token,message)
        elif  action=='ReUpdate':
            message = TextSendMessage(
                        text = '請重新輸入要修改的份量數:'
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
            elif value=='selfInfo':
                viewOrUpdateUserInfo(event,user_id)
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
            record_id,food_name,date=value.split(':')
            updateQuantity(event, user_id, food_name, record_id, date)
        elif action =='record':
            if value=='name':
                None
            elif value=='cancle':
                if user_id in filling_imgInfo:
                    filling_imgInfo.pop(user_id)
            elif value=='reinput':
                message = TextSendMessage(
                            text = '請重新輸入要紀錄的份量數:'
                    )
                line_bot_api.reply_message(event.reply_token,message)
            elif value[:7]=='comfirm':
                act,value=value.split(':')
                success=db_using.recordImgData2DB(user_id, value,filling_imgInfo[user_id].get('name'),filling_imgInfo[user_id].get('data'))
                if success:
                    message = TextSendMessage(
                                text = "紀錄新增成功"
                        )
                    line_bot_api.reply_message(event.reply_token,message)
                    filling_imgInfo.pop(user_id)
                else:
                    line_bot_api.reply_message(event.reply_token,'紀錄發生錯誤')
            elif value[:7]=='imgData':
                value,result=value.split(';')
                filling_imgInfo[user_id]={'name':None,'data':eval(result)}
                message = TextSendMessage(
                            text = "請輸入食物名稱",
                            quick_reply=(QuickReply(
                            items=[
                                {
                                      "type": "action",
                                      "action": {
                                        "type": "postback",
                                        "label": "開始輸入",
                                        'data':"record^name",
                                        'inputOption':'openKeyboard',
                                        'fillInText':'名稱:'
                                      }
                                    },
                                    {
                                      "type": "action",
                                      "action": {
                                        "type": "postback",
                                        "label": "取消",
                                        'data':"record^cancle",
                                        'text':'取消輸入',
                                      }
                                    }
                                ]
                            )
                        )
                    )
                line_bot_api.reply_message(event.reply_token,message)
            else:
                _value,quantity=value.split(':')
                if quantity=='other':
                    message = TextSendMessage(
                                text = '請輸入自訂份量數字:',
                                quick_reply=(QuickReply(
                                items=[
                                    QuickReplyButton(
                                    action=PostbackAction(label="取消輸入",data='record^cancle')
                                                )
                                    ]
                                )
                            )
                        )
                    line_bot_api.reply_message(event.reply_token,message)
                else:
                    success=db_using.recordImgData2DB(user_id, quantity,filling_imgInfo[user_id].get('name'),filling_imgInfo[user_id].get('data'))
                    if success:
                        message = TextSendMessage(
                                    text = "紀錄新增成功"
                            )
                        line_bot_api.reply_message(event.reply_token,message)
                        filling_imgInfo.pop(user_id)
                    else:
                        line_bot_api.reply_message(event.reply_token,'紀錄發生錯誤')
        elif action == 'confirm':
            if value[:2]=="dl":
                temp=value[3:]
                print(temp)
                delete_data_call(event,temp,user_id)

def recordImgData(event,user_id,data):
    if data[:3]=='名稱:':
        name=data[3:]
        if len(name)<=10:
            filling_imgInfo[user_id]['name']=name
            print(filling_imgInfo[user_id])
            askingImgDataQuantity(event,data,user_id)
    elif(data in ['確認紀錄',"添加到我的紀錄","紀錄 1 份","紀錄 2 份","紀錄 3 份","紀錄 0.5 份"]):
        None
    elif (isFloat(data)==False or data.isnumeric()==False):
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
    elif data.isdigit() or (data.count('.') == 1 and data.replace('.', '').isnumeric()):
        value = float(data)
        if value <= 0:
            message = TextSendMessage(
                        text = '請輸入大於0的正數',
                        quick_reply=(QuickReply(
                        items=[
                            QuickReplyButton(
                            action=PostbackAction(label="取消輸入",data='record^cancle')
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
                            action=PostbackAction(label="是",data='record^reinput')
                                        ),
                            QuickReplyButton(
                            action=PostbackAction(label="否",data=f"record^comfirm:{value}",text='確認紀錄')
                                        )
                            ]
                        )
                )
            )
        else:
            message = TextSendMessage(
                        text = f'紀錄 {value} 份?',
                        quick_reply=(QuickReply(
                        items=[
                            QuickReplyButton(
                            action=PostbackAction(label="確認",data=f'record^comfirm:{value}',text='確認紀錄')
                                        ),
                            QuickReplyButton(
                            action=PostbackAction(label="重新輸入",data='record^reinput')
                                        ),
                            QuickReplyButton(
                            action=PostbackAction(label="取消",data="record^cancle")
                                        )
                            ]
                        )
                    )
                )
            
        line_bot_api.reply_message(event.reply_token,message)

    
def showImgResult(event,user_id,result):
    message = message=FlexSendMessage(
                alt_text='圖像辨識結果',
                contents={
                  "type": "bubble",
                  "size": "hecto",
                  "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "text",
                        "text": '辨識結果',
                        "size": "xl",
                        "margin": "sm"
                      }
                    ]
                  },
                  "hero": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "separator"
                      },
                      {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                              "type": "text",
                              "text":"每一份量 : " +result.get('每一份量')
                            },
                            {
                              "type": "text",
                              "text":"包裝份量 : " +result.get('包裝份量') +" 份"
                            },
                          {
                            "type": "text",
                            "text":"熱量 : " +result.get('熱量') +" 大卡"
                          },
                           {
                             "type": "text",
                             "text":"蛋白質 : " + result.get('蛋白質') +" 公克"
                           },
                           {
                             "type": "text",
                             "text": "脂肪 : " +result.get('脂肪') +" 公克"
                           },
                           {
                             "type": "text",
                             "text":"碳水化合物 : " + result.get('碳水化合物') +" 公克"
                           }
                        ],
                        "spacing": "md",
                        "margin": "xxl",
                        "position": "relative",
                        "borderWidth": "semi-bold",
                        "cornerRadius": "none",
                        "paddingStart": "xxl"
                      },
                      {
                        "type": "separator",
                        "margin": "xxl"
                      }
                    ]
                  },
                  "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "button", 
                        "action":{
                        "type":"postback",
                        "label": "加到我的紀錄",
                        "data": "record^imgData;"+str(result),
                        "text":"添加到我的紀錄"
                        }
                      }
                    ]
                  }
                }
            )
    line_bot_api.reply_message(event.reply_token,message)
    
def loading2GPT(event,prompt,user_id):
    reply=chat.UsingChat(user_id, chatMode[user_id].get('data'),prompt)
    message = TextSendMessage(
                text = reply
        )
    line_bot_api.reply_message(event.reply_token,message)
    

def reply2User(event,reply,user_id):
    message = TextSendMessage(
                text = "請稍待訊息回覆!"
        )
    line_bot_api.reply_message(event.reply_token,message)
      
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


def viewOrUpdateUserInfo(event,user_id): 
    
    message = TemplateSendMessage(
            alt_text="觀看個人資料",
            template=ButtonsTemplate(
                title="查看個人資料",
                text="點擊下面的按鈕開啟表單\n可察看個人資料，或進行修改",
                actions=[
                    URIAction(
                        label="個人資料",
                        uri="https://liff.line.me/"+liffid_viewUserInfo
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
    if (len(result)==0 or result=='noTable'):
        message = TextSendMessage(
                    text = "您今天尚未創建任何紀錄!"
            )
        line_bot_api.reply_message(event.reply_token,message)
    else:
        # 創建最終的 JSON 物件
        flex_content=record.bubble_creat(len(result),result)
        message=[
                TextSendMessage(
                        text = '今日紀錄'
                ),
            FlexSendMessage(
                alt_text='紀錄',
                contents=flex_content
        )
        ]
        line_bot_api.reply_message(event.reply_token, message)

def view_specific_day_record(event,date,user_id):
    print(date)
    result=db.queryfromDB(date, user_id)
    if (len(result)==0):
        message = TextSendMessage(
                    text = f"{date}\n未取得任何紀錄!"
            )
        line_bot_api.reply_message(event.reply_token,message)
    elif result == 'noTable':
        message = TextSendMessage(
                    text = f"{date}\n未建立任何紀錄!"
            )
        line_bot_api.reply_message(event.reply_token,message)
    else:
        # 創建最終的 JSON 物件
        flex_content=record.bubble_creat(len(result),result)
        message=[
            TextSendMessage(
                        text = f'{date} 紀錄'
                ),
            FlexSendMessage(
                    alt_text='紀錄',
                    contents=flex_content
            )
        ]
        line_bot_api.reply_message(event.reply_token, message)

def updateQuantity(event,user_id,food_name,record_id,date):
    message = TextSendMessage(
                text = f"修改 {food_name} 份量\n請直接輸入要修改的份量數:"
        )
    udQuantity[user_id]={'id':record_id,'name':food_name,'date':date}
    
    line_bot_api.reply_message(event.reply_token,message)
    
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
    if success==True:
        message = TextSendMessage(
                    text = "刪除記錄成功"
            )
        line_bot_api.reply_message(event.reply_token,message)
    elif success=='此筆資料已不存在，無法進行刪除操作':
        message = TextSendMessage(
                    text = '此筆資料已不存在\n無法進行刪除操作\n請先確認紀錄後再執行此操作!'
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
        
def askingQuantity(event,food_id,food_name,user_id):
    filling_quantity[user_id]={
        'foodid':food_id
        }
    message = TextSendMessage(
               text = f'紀錄 {food_name}\n請選擇要記錄的份量數',
               quick_reply=(QuickReply(
               items=[
                   QuickReplyButton(
                   action=PostbackAction(label="0.5份", data=f"recordWithQuantity^{food_id}:0.5",text='紀錄 0.5 份')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="1份", data=f"recordWithQuantity^{food_id}:1",text='紀錄 1 份')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="2份", data=f"recordWithQuantity^{food_id}:2",text='紀錄 2 份')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="3份", data=f"recordWithQuantity^{food_id}:3",text='紀錄 3 份')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="自訂份量", data=f"recordWithQuantity^{food_id}:other",inputOption='openKeyboard')
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
def askingImgDataQuantity(event,keyword,user_id):
    message = TextSendMessage(
               text = '請選擇要記錄的份量數',
               quick_reply=(QuickReply(
               items=[
                   QuickReplyButton(
                   action=PostbackAction(label="0.5份", data="record^quantity:0.5",text='紀錄 0.5 份')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="1份", data="record^quantity:1",text='紀錄 1 份')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="2份", data="record^quantity:2",text='紀錄 2 份')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="3份", data="record^quantity:3",text='紀錄 3 份')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="自訂份量", data="record^quantity:other",inputOption='openKeyboard',fillInText='份量:')
                               ),
                   QuickReplyButton(
                   action=PostbackAction(label="取消輸入",data='record^cancle')
                       )
                   ]
               )
           )
        )       
    line_bot_api.reply_message(event.reply_token,message)

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
            if user_id in filling_quantity:    
                filling_quantity.pop(user_id)
                message = TextSendMessage(
                            text = '記錄新增成功'
                    )
            
            line_bot_api.reply_message(event.reply_token,message)
def isFloat(num):
    try:
        float(num)
        return True
    except:
        return False
def recordWithCQ(event,keyword,user_id):
    food_id=filling_quantity[user_id].get('foodid')
    if(keyword in ["添加到我的紀錄","紀錄 1 份","紀錄 2 份","紀錄 3 份","紀錄 0.5 份"]):
        None
    elif(keyword=='確認紀錄'):
        if user_id in filling_quantity:
            filling_quantity.pop(user_id)
    elif (isFloat(keyword)==False):
        if(keyword.isnumeric==False):
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
    elif keyword.isdigit() or (keyword.count('.') == 1 and keyword.replace('.', '').isnumeric()):
        value = float(keyword)
        if value <= 0:
            message = TextSendMessage(
                        text = '請輸入大於0的正數',
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

def updateWithCQ(event,quantity,user_id):
    id=udQuantity[user_id].get('id')
    name=udQuantity[user_id].get('name')
    date=udQuantity[user_id].get('date')
    if(quantity=='確認修改'):
        if user_id in udQuantity:
            udQuantity.pop(user_id)
    elif (isFloat(quantity)==False):
        if(quantity.isnumeric==False):
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
    elif quantity.isdigit() or (quantity.count('.') == 1 and quantity.replace('.', '').isnumeric()):
        value = float(quantity)
        if value <= 0:
            message = TextSendMessage(
                        text = '請輸入大於0的正數',
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
                            action=PostbackAction(label="是",data='ReUpdate^{quantity}')
                                        ),
                            QuickReplyButton(
                            action=PostbackAction(label="否",data=f"Update^{user_id}:{id}:{name}:{quantity}:{date}",text='確認修改')
                                        )
                            ]
                        )
                )
            )
        else:
            message = TextSendMessage(
                        text = f'紀錄 {value} 份?',
                        quick_reply=(QuickReply(
                        items=[
                            QuickReplyButton(
                            action=PostbackAction(label="確認",data=f'Update^{id}:{name}:{quantity}:{date}',text='確認修改')
                                        ),
                            QuickReplyButton(
                            action=PostbackAction(label="重新輸入",data='ReUpdate^{quantity}')
                                        ),
                            QuickReplyButton(
                            action=PostbackAction(label="取消",data=f"CancleUpdate^{user_id}")
                                        )
                            ]
                        )
                    )
                )
            
        line_bot_api.reply_message(event.reply_token,message)

if __name__ == '__main__':
    app.run()
