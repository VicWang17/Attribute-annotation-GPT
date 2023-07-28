from flask import Flask
from flask import Blueprint
from flask import request
import requests
import json

beimin = Blueprint("beimin",__name__)
app = Flask(__name__)

@beimin.route("index",methods=["POST"])               #入口
def index():
    try:
        
        method = "属性标注" #因为我这没有method的数据
        
        input = request.json.get("input")
        association = request.json.get("association")
        conversation_association = request.json.get("conversation_association")
        history = request.json.get("history")
        attribute = request.json.get("attribute")
        try:
            data = cognition_fun(input, association, conversation_association, history, attribute)
        except Exception as e:
            app.logger.info('gpt请求报错')
            app.logger.info(e)
            status = -100
            data = {"method": method, "status": status, "flag": 0, "response": ""}
    except Exception as e:
        app.logger.info('参数报错')
        app.logger.info(e)
        status = -2
        data = {"method": method, "status": status, "flag": 0, "response": ""}
    return data

def cognition_fun(input,association,conversation_association,history,attribute):
    gpt_api_url="http://172.16.3.175:9999/gptService/v1/sentenceZH"

    headers = {
        "Content-Type": "application/json"
    }
    data={}
    data["method"] = "属性标注"
    data["flag"] = 0
    prompt=""
    try:
        new_attribute=[]
        for item in attribute:
            if item not in new_attribute:
                new_attribute.append(item)
        attribute=new_attribute
        if len(attribute)==0:
            app.logger.info(attribute)
            app.logger.info('属性列表为空')
            data["status"] = 1
            data["response"] = []
            return data
        attribute_instruction="给定属性："
        prompt+=attribute_instruction
        for item in attribute[:-1]:
            prompt+=item+','
        prompt+=attribute[-1]+'。'
    except Exception as e:
        app.logger.info(e)
        app.logger.info('属性报错')
        data["status"] = -2
        data["response"] = []
        return data
    prompt+='\n'
    
    instruction="根据以上属性，分析给定文本中是否有能够判断这些属性的词语，找出这些词语，并且回答文本中的词语，如果没有就回答无\n"
    prompt+=instruction
    style_instruction = "文本: 夏琴是谁\n回答: 无\n文本: 我很生气！好烦啊。\n回答: 生气、烦"
    prompt+=style_instruction
    try:
        if len(history)!=0:
            question=history[-1]
            if 'AI:' in question:
                question=question.split('AI:')[1]
                prompt+="问题："
                prompt+=question+'\n'
    except Exception as e:
        app.logger.info('历史报错')
        app.logger.info(e)
        data["status"] = -2
        data["response"] = []
        return data
    try:
        
        prompt+="文本："
        if input[-1]!='。':
            input+='。'
        prompt+=input+'\n'+'词语：'
    except Exception as e:
        app.logger.info('输入报错')
        app.logger.info(e)
        data["status"] = -2
        data["response"] = []
        return data
    gpt_data = {}
    gpt_data['method'] = "gptChatReq"
    gpt_data['messages'] = [{'role': 'system', 'content': prompt}]
    gpt_data['model'] = 'gpt-3.5-turbo'
    
    gpt_data['temperature'] = 0.0
    gpt_data['stop']=["。"]
    app.logger.info(prompt)
    app.logger.info('gpt_data:')
    app.logger.info(gpt_data)
    try:
        response = requests.post(gpt_api_url, headers=headers, data=json.dumps(gpt_data))
    except Exception as e:
        app.logger.info(e)
        app.logger.info('调用铭星gpt出错')
        data["status"] = -100
        data["response"] = []
        return data
    try:
        result_data = json.loads(response.text)
        result_data = result_data['data']
        choices = result_data['response']
        result = choices
        app.logger.info(response)
        
        prompt = "用户:"+input+"\n线索词:"+result+"\n答案可能有多个, 答案之间用逗号(,)隔开。根据线索词,用户的话表达了以下哪个词语哪些词语? 无、"
        for item in attribute[:-1]:
            prompt+=item+','
        prompt+=attribute[-1]+'。'
        gpt_data['messages'] = [{'role': 'system', 'content': prompt}]
        response = requests.post(gpt_api_url, headers=headers, data=json.dumps(gpt_data), timeout=30)
        result_data = json.loads(response.text)
        result_data = result_data['data']
        choices = result_data['response']
        response = choices

        rlist = response.split(",")
        response_list = []
        for r in rlist:
            response_list.append(r)
    except Exception as e:
        app.logger.info(e)
        app.logger.info('gpt返回格式不符合预期')
        data["status"] = -100
        data["response"] = []
        return data
    data["status"] = 1
    data["result"] = result
    data["response"] = response_list
    return data