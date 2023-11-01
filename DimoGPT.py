import openai
import json
from googlesearch import search
import os

import DB_Control as db

openai.api_key = os.getenv('openai_key')

backtrace = 2   # 記錄幾組對話
def google_res(user_msg, num_results=5, verbose=False):
    content = "以下為已發生的事實：\n"                # 強調資料可信度
    for res in search(user_msg, advanced=True,    # 一一串接搜尋結果
                      num_results=num_results,
                      lang='zh-TW'):
        content += f"標題：{res.title}\n" \
                    f"摘要：{res.description}\n\n"
    content += "請依照上述事實回答以下問題：\n"        # 下達明確指令
    if verbose:
        print('------------')
        print(content)
        print('------------')
    return content

def excerciseAndmeal(user_msg,user_id):
    defaltInfo=db.view_user_info(user_id)
    
    user_info = {}
    user_info['gender'] = defaltInfo[2]
    user_info['height'] = defaltInfo[3]
    user_info['weight'] = defaltInfo[4]
    user_info['exerciseIntensity'] = defaltInfo[5]
    user_info['fitnessGoal'] = defaltInfo[6]
    
    mealList=db.queryfromDB('today', user_id)
    food_had_eat=[]
    if len(mealList)==0 or mealList=='noTable':
        metaPrompt=f''' 我是一位{user_info.get('gender')}、身高:{user_info.get('height')}公分、體重:{user_info.get('weight')}公斤
        平時從事{user_info.get('exerciseIntensity')}運動，想要達成{user_info.get('fitnessGoal')}的體態目標。
        今天還沒有吃過任何東西。
        請根據針對以上個人資訊，並根據下列問題回答至多三項有關於運動或健康飲食的相關建議'''
    else:
        for i in range(len(mealList)):
            food_had_eat.append(mealList[i][4])
        metaPrompt=f''' 我是一位{user_info.get('gender')}、身高:{user_info.get('height')}公分、體重:{user_info.get('weight')}公斤
        平時從事{user_info.get('exerciseIntensity')}運動，想要達成{user_info.get('fitnessGoal')}的體態目標。
        今天已經吃了{food_had_eat}這些東西。
        請根據上述提供的資訊，並根據下列問題回答至多三項有關於運動或健康飲食的相關建議'''
    return metaPrompt
def food_info(food_name):
    metaPrompt='''
    根據現有資料或是利用google_res function搜尋，並用以下格式回應:
        食物名稱:
        熱量:
        蛋白質:
        脂肪:
        碳水化合物:
        (單位若沒有特別指定，皆以常見包裝一份之營養含量為主，熱量單位為大卡，其餘皆為公克)
        
        請根據以上限制回答此問題:
            '''
    return metaPrompt
def eating_method_sugest(user_msg,user_id):
    defaltInfo=db.view_user_info(user_id)
    
    user_info = {}
    user_info['gender'] = defaltInfo[2]
    user_info['height'] = defaltInfo[3]
    user_info['weight'] = defaltInfo[4]
    user_info['exerciseIntensity'] = defaltInfo[5]
    user_info['fitnessGoal'] = defaltInfo[6]
    
    mealList=db.queryfromDB('today', user_id)
    food_had_eat=[]
    if len(mealList)==0 or mealList=='noTable':
        metaPrompt=f''' 我是一位{user_info.get('gender')}、身高:{user_info.get('height')}公分、體重:{user_info.get('weight')}公斤
        平時從事{user_info.get('exerciseIntensity')}運動，想要達成{user_info.get('fitnessGoal')}的體態目標。
        今天還沒有吃過任何東西。
        請根據針對以上個人資訊，給予1~3個重點來回答以下問題:'''
    else:
        for i in range(len(mealList)):
            food_had_eat.append(mealList[i][4])
        metaPrompt=f''' 我是一位{user_info.get('gender')}、身高:{user_info.get('height')}公分、體重:{user_info.get('weight')}公斤
        平時從事{user_info.get('exerciseIntensity')}運動，想要達成{user_info.get('fitnessGoal')}的體態目標。
        今天已經吃了{food_had_eat}這些東西。
        請根據上述提供的資訊，給予1~3個重點來回答以下問題:'''
    return metaPrompt
def resipeOffering(dish_name,user_id):
    metaPrompt=f'''
    根據現有資料或是利用google_res function搜尋，提供{dish_name}的相關食譜或式料理方式
    請給予最多兩種建議。
    '''
    return metaPrompt
def system_intro(user_msg):
    return'你好!這是一個營養資訊系統!'

def meal_sugest(user_msg,user_id):
    defaltInfo=db.view_user_info(user_id)
    
    user_info = {}
    user_info['gender'] = defaltInfo[2]
    user_info['height'] = defaltInfo[3]
    user_info['weight'] = defaltInfo[4]
    user_info['exerciseIntensity'] = defaltInfo[5]
    user_info['fitnessGoal'] = defaltInfo[6]
    
    mealList=db.queryfromDB('today', user_id)
    food_had_eat=[]
    if len(mealList)==0 or mealList=='noTable':
        metaPrompt=f''' 我是一位{user_info.get('gender')}、身高:{user_info.get('height')}公分、體重:{user_info.get('weight')}公斤
        平時從事{user_info.get('exerciseIntensity')}運動，想要達成{user_info.get('fitnessGoal')}的體態目標。
        飲食狀況:今天還沒有吃過任何東西。
        請根據針對以上個人資訊，綜合分析飲食狀況及欲達成之目標，給予1~3個相關的餐食推薦，以回答以下問題:'''
    else:
        for i in range(len(mealList)):
            food_had_eat.append(mealList[i][4])
        metaPrompt=f''' 我是一位{user_info.get('gender')}、身高:{user_info.get('height')}公分、體重:{user_info.get('weight')}公斤
        平時從事{user_info.get('exerciseIntensity')}運動，想要達成{user_info.get('fitnessGoal')}的體態目標。
        飲食狀況:今天已經吃了{food_had_eat}這些東西。
        請根據針對以上個人資訊，綜合分析飲食狀況及欲達成之目標，給予1~3個相關的餐食推薦，以回答以下問題:'''
    return metaPrompt
func_table = [
    {                       # 每個元素代表一個函式
        "chain": True,      # 函式執行結果是否要再傳回給 API
        "func": google_res, # 函式
        "spec": {           # function calling 需要的函式規格
            "name": "google_res",
            "description": "以 Google 搜尋結果回答食品營養資訊、飲食方法或準則、食譜推薦或料理方式、運動及健康飲食相關問題。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_msg": {
                        "type": "string",
                        "description": "要搜尋的關鍵字",
                    }
                },
                "required": ["user_msg"],
            },
        }
    },
    {                       # 每個元素代表一個函式
        "chain": False,      # 函式執行結果是否要再傳回給 API
        "func": system_intro, # 函式
        "spec": {           # function calling 需要的函式規格
            "name": "system_intro",
            "description": "回覆「向使用者打招呼或進行系統簡介」此類型問題",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_msg": {
                        "type": "string",
                        "description": "使用者問題的重點或摘要",
                    }
                },
                "required": ["user_msg"],
            },
        }
    },
    {                       # 每個元素代表一個函式
        "chain": True,      # 函式執行結果是否要再傳回給 API
        "func": food_info, # 函式
        "spec": {           # function calling 需要的函式規格
            "name": "food_info",
            "description": "回覆「食品營養資訊」此類型問題",
            "parameters": {
                "type": "object",
                "properties": {
                    "food_name": {
                        "type": "string",
                        "description": "使用者想要知到營養資訊的食物名稱",
                    }
                },
                "required": ["food_name"],
            },
        }
    },
    {                       # 每個元素代表一個函式
        "chain": True,      # 函式執行結果是否要再傳回給 API
        "func": eating_method_sugest, # 函式
        "spec": {           # function calling 需要的函式規格
            "name": "eating_method_sugest",
            "description": "回覆「飲食方法或準則」此類型問題，提供飲食法，或飲食準則",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_msg": {
                        "type": "string",
                        "description": "使用者想了解的飲食方法或是飲食方向",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "prompt內的argument(user_id)",
                    }
                },
                "required": ["user_msg","user_id"],
            },
        }
    },
    {                       # 每個元素代表一個函式
        "chain": True,      # 函式執行結果是否要再傳回給 API
        "func": resipeOffering, # 函式
        "spec": {           # function calling 需要的函式規格
            "name": "resipeOffering",
            "description": "回覆「食譜推薦或料理方式」此類型問題，提供菜品料理方式或詳細食譜，若使用者語意內包含食物或式菜餚名稱，即可使用次方法",
            "parameters": {
                "type": "object",
                "properties": {
                    "dish_name": {
                        "type": "string",
                        "description": "使用者想知道的食譜名稱或是菜品名稱，必須是一道菜的名稱或是一種料理手法",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "user_id",
                    }
                },
                "required": ["dish_name","user_id"],
            },
        }
    },
    {                       # 每個元素代表一個函式
        "chain": True,      # 函式執行結果是否要再傳回給 API
        "func": excerciseAndmeal, # 函式
        "spec": {           # function calling 需要的函式規格
            "name": "excerciseAndmeal",
            "description": "回覆「運動及健康飲食」此類型問題",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_msg": {
                        "type": "string",
                        "description": "使用者問題的重點或摘要",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "user_id",
                    }
                },
                "required": ["user_msg","user_id"],
            },
        }
    },
    {                       # 每個元素代表一個函式
        "chain": True,      # 函式執行結果是否要再傳回給 API
        "func": meal_sugest, # 函式
        "spec": {           # function calling 需要的函式規格
            "name": "meal_sugest",
            "description": "回覆「飲食建議或料理推薦」此類型問題，根據使用者的問題提給予料理推薦",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_msg": {
                        "type": "string",
                        "description": "使用者想了解的飲食推薦或是料理名稱",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "user_id",
                    }
                },
                "required": ["user_msg","user_id"],
            },
        }
    }
    
    ]



def call_func(func_call):
    func_name = func_call['name']
    args = json.loads(func_call['arguments'])
    for f in func_table: # 找出包含此函式的項目
        if func_name == f['spec']['name']:
            print(f"嘗試叫用：{func_name}(**{args})")
            val = f['func'](**args)
            return val, f['chain']
    return '', False

# 從 API 傳回內容找出 function_calling 內容
def get_func_call(messages, stream=False, func_table=None,
                  **kwargs):
    model = 'gpt-3.5-turbo'
    if 'model' in kwargs: model = kwargs['model']
    funcs = {}
    if func_table:
        funcs = {'functions':[f['spec'] for f in func_table]}
    response = openai.ChatCompletion.create(
        model = model,
        messages = messages,
        stream = stream,
        **funcs
    )
    if stream:
        chunk = next(response)
        delta = chunk["choices"][0]["delta"]
        if 'function_call' in delta:
            func_call = delta['function_call']
            args = ''
            for chunk in response:
                delta = chunk["choices"][0]["delta"]
                if 'function_call' in delta:
                    args += delta['function_call']['arguments']
            func_call['arguments'] = args
            return func_call, None
    else:
        msg = response["choices"][0]["message"]
        if 'function_call' in msg:
            return msg['function_call'], None
    return None, response


def get_reply_f(messages, stream=False, func_table=None, **kwargs):
    try:
        func_call, response = get_func_call(messages,stream, func_table, **kwargs)
        if func_call:
            res, chain = call_func(func_call)
            if chain:  # 如果需要將函式執行結果送回給 AI 再回覆
                messages += [
                    {  # 必須傳回原本 function_calling 的內容
                        "role": "assistant", "content": None,
                        "function_call": func_call
                    },
                    {  # 以及以 function 角色的函式執行結果
                        "role": "function",        # function 角色
                        "name": func_call['name'], # 傳回函式名名稱
                        "content": res             # 傳回執行結果
                    }]
                yield from get_reply_f(messages, stream,func_table, **kwargs)
            else:      # chain 為 False, 以函式叫用結果當成模型生成內容
                yield res
        elif stream:   # 不需叫用函式但使用串流模式
            for chunk in response:
                if 'content' in chunk['choices'][0]['delta']:
                    yield chunk['choices'][0]['delta']['content']
        else:          # 不需叫用函式也沒有使用串流模式
            yield response['choices'][0]['message']['content']
    except openai.OpenAIError as err:
        reply = f"發生 {err.error.type} 錯誤\n{err.error.message}"
        print(reply)
        yield reply

def chat_f(hist,sys_msg, user_msg, stream=False, **kwargs):
    
    print(f"""=================================== 
          {hist}
          ===================================""")
    replies = get_reply_f(    # 使用函式功能版的函式
        hist                  # 先提供歷史紀錄
        + [{"role": "user", "content": user_msg}]
        + [{"role": "system", "content": sys_msg}],
        stream, func_table, **kwargs)
    reply_full = ''
    for reply in replies:
        reply_full += reply
        yield reply

    hist += [{"role":"user", "content":user_msg},
             {"role":"assistant", "content":reply_full}]
    while len(hist) >= 2 * backtrace: # 超過記錄限制
        hist.pop(0)  # 移除最舊的紀錄
    
def UsingChat(user_id,hist,user_msg):  
    userInfo=db.view_user_info(user_id)
    mealList=db.queryfromDB('today', user_id)
    print(mealList)
    print(userInfo)
    print(user_id +'is in chatting mode')
    print('Hist='+str(hist))
    
    # sys_msg = '你是一位語意辨識人員，請根據主題列表判斷問題類別，並根據判斷之類別選擇回覆方式。\n主題列表:[向使用者打招呼或進行系統簡介、食品營養資訊、飲食方法或準則、食譜推薦或料理方式、運動及健康飲食]\n若使用者之問題與可回覆之類別皆不相關，請回答:「此問題與本系統無關，無法回應。」'
    sys_msg = '請執行語意判斷工作，針對使用者提出的語句，根據主題列表判斷問題類別並選擇相對應的回覆方式。\n若無法選擇相關的function進行回覆，請回答:「此問題與本系統無關，無法回應。」\n主題列表:[向使用者打招呼或進行系統簡介、食品營養資訊、飲食方法或準則、食譜推薦或料理方式、運動及健康飲食]。'
    prompt=f'argument:user_id={user_id};main question:'
    prompt+=user_msg
    for reply in chat_f(hist,sys_msg, prompt, stream=False):
            
            return reply
            
if __name__=='__main__':
    reply=UsingChat('Ub5136c58845e8760da3979c36d8dbb5b',[], '晚餐吃什麼?')
    print(reply)
