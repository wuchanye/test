# -*- coding: utf-8 -*-
"""
Created on Tue Oct 10 04:21:26 2023

@author: harry
"""
import DB_Control as db

def item_create(index,block,data):
    item={
            block: {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                 "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": f"{data[index][4]}",
                "weight": "bold",
                "size": "md",
                "wrap": True,
                "flex": 7
              },
              {
                "type": "text",
                "text": f"份數: {data[index][10]}",
                "size": "xxs",
                "flex": 3,
                "align": "start",
                "gravity": "bottom",
                "offsetTop": "xs"
              }
            ],
                "height": "20px",
                "flex": 2
                },
                {
                "type": "separator",
                "margin": "sm"
                },
                {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                        "type": "text",
                        "text": "熱量",
                        "size": "xs"
                        },
                        {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                            "type": "filler"
                            }
                        ],
                        "height": "6px",
                        "width": f"{(data[index][6]*data[index][10])/10}%",
                        "backgroundColor": "#000000"
                        }
                    ],
                    "height": "22px"
                    },
                    {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                        "type": "text",
                        "text": "蛋白質",
                        "size": "xs"
                        },
                        {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                            "type": "filler"
                            }
                        ],
                        "height": "6px",
                        "width": f"{(data[index][7]*data[index][10])/10}%",
                        "backgroundColor": "#000000"
                        }
                    ],
                    "height": "22px"
                    },
                    {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                        "type": "text",
                        "text": "脂肪",
                        "size": "xs"
                        },
                        {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                            "type": "filler"
                            }
                        ],
                        "height": "6px",
                        "width": f"{(data[index][8]*data[index][10])/10}%",
                        "backgroundColor": "#000000"
                        }
                    ],
                    "height": "22px"
                    },
                    {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                        "type": "text",
                        "text": "碳水化合物",
                        "size": "xs"
                        },
                        {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                            "type": "filler"
                            }
                        ],
                        "height": "6px",
                        "width": f"{(data[index][9]*data[index][10])/10}%",
                        "backgroundColor": "#000000"
                        }
                    ],
                    "height": "22px"
                    }
                ],
                "margin": "sm",
                "spacing": "xs",
                "flex": 6
                },
                {
                "type": "separator",
                "margin": "md"
                },
                {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "修改",
                        "data": "udRecord^"+str(data[index][0])+":"+data[index][4]+":"+str(data[index][2])
                    },
                    "flex": 5,
                    "height": "sm"
                    },
                    {
                    "type": "separator"
                    },
                    {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "刪除",
                        "data": "dlRecord^"+str(data[index][0])+":"+data[index][4]+":"+str(data[index][2])
                    },
                    "flex": 5,
                    "height": "sm"
                    }
                ],
                "spacing": "xs",
                "flex": 2
                },
                {
                "type": "separator",
                }
            ],
            "height": "180px",
            "paddingAll": "8px"
                      }
            }
    return item

def bubble_creat(num,data):
    index=0
    circle_time=3
    
    block=["header","hero","body"]
    quotient, remainder= divmod(num, 3)
    flex_content={
          "type": "carousel",
          "contents": [
          ]
        }
    #for quotient
    if remainder==0:
        for i in range(0,quotient):
            bubble_content={}
            for j in range(circle_time):
                if j==0:
                    bubble_content.update({"type": "bubble"})
                    bubble_content.update({"size": "micro"})
                bubble_content.update(item_create(index,block[j],data))
                index+=1
            flex_content["contents"].append(bubble_content)
        
        return flex_content
    else:
        for i in range(0,quotient+1):
            bubble_content={}
            if i == (quotient):               
                circle_time=remainder
            print(circle_time)
            for j in range(circle_time):
                if j==0:
                    bubble_content.update({"type": "bubble"})
                    bubble_content.update({"size": "micro"})
                bubble_content.update(item_create(index,block[j],data))
                index+=1
            flex_content["contents"].append(bubble_content)
        
        return flex_content