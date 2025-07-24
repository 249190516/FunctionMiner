from zhipuai import ZhipuAI

import json


class zhipuLLM:
    def __init__(self):
        self.client = ZhipuAI(api_key="60ac89773bd92796cf4e736a298a401a.bXnS1lqhCPk9Bsse")
        self.tools = [{
            "type": "web_search",
            "web_search": {
                "enable": False
            }
        }]

        with open('config.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        self.messages = [
            {
                "role": "system",
                "content": data['0']
            }
        ]
        self.callCount = 0

    def addAssistantMessage(self, content):
        message = {
            "role": "assistant",
            "content": content
        }
        self.messages.append(message)

    def addUserMessage(self, content):
        message = {
            "role": "user",
            "content": content
        }
        self.messages.append(message)

    def resetMessages(self):
        with open('config.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        self.messages = [
            {
                "role": "system",
                "content": data['0']
            }
        ]

    def getResponse(self):
        response = self.client.chat.completions.create(
            # model="glm-4-plus",
            model="glm-4-flash",
            messages=self.messages,
            tools=self.tools,
            top_p=0.7,
            temperature=0.95,
        )
        self.addAssistantMessage(response.choices[0].message.content)
        return response.choices[0].message.content


if __name__ == '__main__':
    zhipu = zhipuLLM()
    zhipu.addUserMessage("你好")
    print(zhipu.getResponse())
