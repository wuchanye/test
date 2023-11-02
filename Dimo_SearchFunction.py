# -*- coding: utf-8 -*-
"""
Created on Sat Apr 29 15:35:14 2023

@author: harry
"""
from linebot.models import QuickReplyButton,MessageAction,PostbackAction,QuickReply, MessageEvent, TextMessage, PostbackEvent, TextSendMessage, TemplateSendMessage, ConfirmTemplate, MessageTemplateAction, ButtonsTemplate, PostbackTemplateAction, URITemplateAction, CarouselTemplate, CarouselColumn, ImageCarouselTemplate, ImageCarouselColumn, FlexSendMessage
import DB_Control as db
import os
from linebot import LineBotApi
import rolltools_api_0717 as api

db_using=db
line_bot_api = LineBotApi(os.environ.get('line_channel_token'))

credential_pool = [
    {'appid':'uxnxyhgkujxpgqbt','secret':'UHJqRjR6S25DaSttRWxZUElSbnovUT09'},
    {'appid':'ljsuumpnlndfcgkp','secret':'shA51m3OLRkHsloqJOBYmJupEHaFR6XT'},
    # 添加更多的認證
]

current_credential_index = 0  # 初始使用第一組認證

# 用來取得下一組認證的函數
def get_next_credential():
    global current_credential_index
    credential = credential_pool[current_credential_index]
    current_credential_index = (current_credential_index + 1) % len(credential_pool)
    return credential

def queryTheDetail(event,mtext,user_id):
    keyword=mtext
    credential = get_next_credential()
    result,img=api.query(credential.get('appid'),credential.get('secret'),keyword,True,True)
    message=FlexSendMessage(
                alt_text='食品詳細資訊',
                contents={
                  "type": "bubble",
                  "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "text",
                        "text": result.get('name'),
                        "size": "xl",
                        "margin": "sm"
                      },
                      {
                        "type": "image",
                        "url": f"{img}",
                        "size": "5xl",
                        "align": "center"
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
                            "text":"熱量 : " +result.get('calory')
                          },
                           {
                             "type": "text",
                             "text":"蛋白質　: " + result.get('protein')
                           },
                           {
                             "type": "text",
                             "text": "脂肪 : " +result.get('fat')
                           },
                           {
                             "type": "text",
                             "text":"碳水化合物 : " + result.get('carb')
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
                        "data": "addrecord^"+keyword+':'+result.get('name'),
                        "text":"添加到我的紀錄"
                        }
                      }
                    ]
                  }
                }
            )
    
    line_bot_api.reply_message(event.reply_token,message)
    

def searching(event, _mtext, user_id):
    keyword=_mtext
    credential = get_next_credential()
    result=api.search(credential.get('appid'),credential.get('secret'),keyword)
    columns=[]
    message=[]
            
    if result==None:
       message = TextSendMessage(
                                text = '目前還沒有相關的食物資料！'
                        )        
    else:
        for index in range(len(result)):
            temptext="熱量 : "+str(result[index].get('calory'))
            
        
            columns.append(CarouselColumn(
                title='{}'.format(result[index].get('name')),
                text=temptext,
                actions=[
                    {
                    'type':'postback',
                    'label':'查看進階資料',                    
                    'data':'searchDetail^{}' .format(result[index].get('foodId')),
                    'text':'搜尋中，請稍待...'
                    }
                
                ],
                )
                )
                
            
        
        message.append(TemplateSendMessage(
            alt_text='食物選擇轉盤',
            template=CarouselTemplate(columns)
            )
        )
        
            
    line_bot_api.reply_message(event.reply_token,message)

