import os
import re
import difflib
import xmltodict

from nlp import Nlp


def strMatch(text1, text2):
    # 使用 SequenceMatcher 找到相似度
    if text1 in text2 or text2 in text1:
        return 10
    sequence_matcher = difflib.SequenceMatcher(None, text1, text2)
    matching_blocks = sequence_matcher.get_matching_blocks()
    max_size = max(block.size for block in matching_blocks)
    return max_size


def setList(indices_to_remove):
    indices_to_remove.sort()
    indices_to_remove_set = [indices_to_remove[0]]
    for num in indices_to_remove[1:]:
        if num != indices_to_remove_set[-1]:
            indices_to_remove_set.append(num)
    return indices_to_remove_set


# 在初始化一个Action时，获取点击位置下所有部分的文本
def getAllActionText(resourceID, hierarchy):
    res = [hierarchy]
    components_str = ''

    while res:
        currentNode = res.pop(0)
        if 'node' in currentNode:
            if type(currentNode['node']).__name__ == 'dict':
                res.insert(0, currentNode['node'])
            else:
                for Node in currentNode['node']:
                    res.insert(0, Node)
        if '@resource-id' in currentNode and resourceID in currentNode['@resource-id']:
            res.clear()
            res.append(currentNode)
            break

    while res:
        currentNode = res.pop(0)
        if '@resource-id' in currentNode:
            components_str += currentNode['@text'] + ' '
        if 'node' in currentNode:
            if type(currentNode['node']).__name__ == 'dict':
                res.insert(0, currentNode['node'])
            else:
                for Node in currentNode['node']:
                    res.insert(0, Node)
    return components_str


# 状态类
class State:
    def __init__(self, time, activityName, fragmentList, hierarchy):
        self.time = time
        self.activityName = activityName
        self.fragmentList = fragmentList
        self.dialogName = ''
        self.hierarchy = hierarchy

        self.stateHash = None
        self.stateContentHash = None
        # 存放出边的列表,指向可以到达的状态
        self.edgeList = []
        self.visited = False
        self.splitIndex = False

    # 为了简化==操作而重写的比较函数
    def __eq__(self, test_case_state):
        # self 是来自模型的state
        if self.dialogName != '':
            stateStr = self.dialogName.lower()
        # elif self.fragmentList:
        #     stateStr = ' '.join(self.fragmentList).lower()
        else:
            stateStr = self.activityName.lower()
        otherStr = test_case_state.activityName.lower()

        # print("state比较  （1）模型/自动化测试: {}  （2）测试用例集: {}".format(stateStr, otherStr))
        if strMatch(stateStr, otherStr) > 4:
            # print("匹配state  （1）模型/自动化测试: {}  （2）测试用例集: {}".format(stateStr, otherStr))
            return strMatch(stateStr, otherStr) * 10
        else:
            return Nlp.getSimilar(stateStr, otherStr)

    def assertMatch(self, test_case_state_assert):
        assert_str = test_case_state_assert.lower()

        if self.dialogName != '':
            dialog_str = self.dialogName.lower()
            if strMatch(dialog_str, assert_str) > 4 or Nlp.getSimilar(dialog_str, assert_str) > 4:
                return True
        # elif self.fragmentList:
        #     fragment_str = ' '.join(self.fragmentList).lower()
        #     if strMatch(fragment_str, assert_str) > 4 or Nlp.getSimilar(fragment_str, assert_str) > 4:
        #         return True
        else:
            activity_str = self.activityName.lower()
            if strMatch(activity_str, assert_str) > 4 or Nlp.getSimilar(activity_str, assert_str) > 4:
                return True
        return False

    def to_dict(self):
        return {
            'time': self.time,
            'activityName': self.activityName,
            # 'fragmentList': self.fragmentList,
            'dialogName': self.dialogName,
        }

    @classmethod
    def from_dict(cls, data):
        temp_state = cls(
            None,
            data,
            [],
            None,
        )
        return temp_state

    def getContentHash(self):
        res = [self.hierarchy]
        components_list = []

        while res:
            currentNode = res.pop(0)
            if 'node' in currentNode:
                if type(currentNode['node']).__name__ == 'dict':
                    res.append(currentNode['node'])
                else:
                    for Node in currentNode['node']:
                        res.append(Node)
            if '@resource-id' in currentNode:
                components_list.append(currentNode['@resource-id'].split('/')[-1])
        self.stateContentHash = hash(''.join(components_list))

    def getComponentsData(self):
        res = [self.hierarchy]
        components_str = ''

        while res:
            currentNode = res.pop(0)
            if 'node' in currentNode:
                if type(currentNode['node']).__name__ == 'dict':
                    res.insert(0, currentNode['node'])
                else:
                    for Node in currentNode['node']:
                        res.insert(0, Node)
            if '@resource-id' in currentNode:
                if 0 < len(currentNode['@content-desc']) < 10:
                    components_str += "{},".format(currentNode['@content-desc'])
                    continue
                elif 0 < len(currentNode['@text']) < 10:
                    components_str += "{},".format(currentNode['@text'])
                    continue
                elif 0 < len(currentNode['@resource-id']) < 20:
                    components_str += currentNode['@resource-id'].split('/')[-1]
        return components_str


# 动作
class Action:
    def __init__(self, time, actionType, text):
        self.actionTime = time
        self.actionType = actionType
        self.text = text

        # 动作触发的函数列表
        self.functionList = []

    def __eq__(self, test_case_action):
        if self.actionType != test_case_action.actionType:
            # print("action比较  （1）模型/自动化测试的动作: {}  （2）测试用例集的动作: {}".format(self.actionType, test_case_action.actionType))
            return 0
        else:
            actionStr = self.text.lower()
            otherStr = test_case_action.text.lower()
            if actionStr == '':
                return 0
            if strMatch(actionStr, otherStr) > 4:
                # print("匹配action  （1）动作: {}  （2）模型/自动化测试的目标: {}  （3）测试用例集的目标: {}  （4）strMatch结果：{}".format(self.actionType, actionStr, otherStr, strMatch(actionStr, otherStr)))
                return strMatch(actionStr, otherStr)
            else:
                return Nlp.getSimilar(actionStr, otherStr)

    def to_dict(self):
        return {
            'actionTime': self.actionTime,
            'actionType': self.actionType,
            'text': self.text
        }

    @classmethod
    def from_dict(cls, data):
        actionType, text = data.split(' ', 1)
        if "点击" in actionType:
            actionType = "CLICK"
        elif "长按" in actionType:
            actionType = "LONG_CLICK"
        elif "滑动" in actionType:
            actionType = "SCROLL"
        action = cls(
            None,
            actionType,
            text
        )
        return action


# 触发的函数
class Function:
    def __init__(self, functionName, packageName):
        self.functionName = functionName
        self.packageName = packageName


# 转换类，边
class Edge:
    def __init__(self, action, state):
        self.action = action
        self.state = state


# 焦点范围判断是否存在弹窗
def transDialog(temp_state_list, index, dialogName):
    bounds = temp_state_list[index].hierarchy['node']['@bounds']
    pattern = r"^(?!\[0,0\]).*"
    match = re.match(pattern, bounds)
    if match:
        for i, state in enumerate(temp_state_list[index:len(temp_state_list) - 1]):
            if re.match(pattern, state.hierarchy['node']['@bounds']):
                temp_state_list[index + i].dialogName = dialogName
    else:
        return


class Model:
    stateList = []
    actionList = []
    UTG = []

    def __init__(self, package):
        self.package = package
        self.path = os.path.join('result', self.package)

        self.initModel()

    def initModel(self):
        for index in range(4):
            temp_action_list = []
            temp_state_list = []
            # 获取actionTrace与XML里的信息
            self.path = os.path.join('result', self.package, str(index))
            path = os.path.join(self.path, "actionTrace.txt")
            with open(path, "r", encoding="utf-8") as file:
                lines = file.readlines()
                action_block = []
                # 定义时间变量的正则表达式模式
                time_pattern = r"\d{2}:\d{2}:\d{2}:\d{3}"
                for line in lines:
                    if re.search(time_pattern, line):
                        if action_block:  # 如果当前记录块不为空，则将其添加到记录块列表中
                            self.getOneActionData(action_block, temp_action_list, temp_state_list)  # 处理一个记录块的一个动作信息
                            action_block = []  # 清空当前记录块
                    action_block.append(line)
                # 添加最后一个记录块
                if action_block:
                    self.getOneActionData(action_block, temp_action_list, temp_state_list)  # 处理一个记录块的一个动作信息
            # 获取Log里的信息
            self.getFunction(temp_action_list, temp_state_list)

            self.actionList.extend(temp_action_list)
            self.stateList.extend(temp_state_list)

        # 状态删减与合并
        self.mergeState()

    # 获取一个动作的相关信息，包括动作本身的信息，执行动作前的界面的信息
    def getOneActionData(self, current_block, temp_action_list, temp_state_list):
        # 获取动作本身信息
        time_pattern = r'(\d{2}:\d{2}:\d{2}:\d{3})'
        actionTime = re.search(time_pattern, current_block[0]).group()
        actionType = current_block[0].split(':')[-1].strip()
        resourceID = current_block[1].strip()
        parts = current_block[1].split('/')
        if len(parts) > 1:
            resourceID = parts[1].strip()
            contentDescription = current_block[2].split("contentDescription:")[1].strip()
            viewText = current_block[3].split("viewText:")[1].strip()
            text = viewText + ' ' + contentDescription + ' ' + resourceID
        else:
            text = ''

        # 获取界面信息的Fragment信息部分
        # 对形如 "20:13:54:170 org.fossify.clock.activities.MainActivity"格式的字符串的拆分，先获取后半段类名，再拆分出最后的活动名
        activity_name = current_block[0].split()[1].split('.')[-1]
        fragment_list = []
        for i, line in enumerate(current_block, start=1):
            if 'mMenuVisible=true' in line:
                temp = current_block[i - 5].split()[0].split("{")[0]
                fragment_list.append(temp)

        # 获取界面信息的XML文件部分,将XML内容获取为content后保存到state中
        file_time = actionTime.replace(':', '-')
        file_name = file_time + '.xml'
        file_path = os.path.join(self.path, file_name)
        with open(file_path, 'r', encoding='utf-8') as file:
            xml_data = file.read()
            hierarchy = xmltodict.parse(xml_data)
        state = State(file_time, activity_name, fragment_list, hierarchy)
        temp_state_list.append(state)

        if text != '':
            text += ' ' + getAllActionText(resourceID, hierarchy).strip()
        action = Action(actionTime, actionType, text)
        temp_action_list.append(action)

    # 获取函数信息
    def getFunction(self, temp_action_list, temp_state_list):
        path = os.path.join(self.path, "Log.txt")
        with open(path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            action_list_index = 0  # Action列表的序号

            for line in lines:
                parts = line.strip().split()
                function_time = parts[0]
                function_name = parts[1]
                package_name = parts[2]

                # 第一个操作之前的函数的处理
                if function_time <= temp_action_list[action_list_index].actionTime:
                    continue
                # 通过字符串匹配的方式对函数进行过滤
                substrings = ["onPause", "onCreate", "onResume", "onDestroy", "onUpdate", "onStart", "onConnect",
                              "invoke", "inflate", "equals", "Same", "is", "get"]
                if all(substring not in function_name for substring in substrings):
                    function = Function(function_name, package_name)
                else:
                    continue
                # 最后一个操作之后的函数的处理
                if function_time > temp_action_list[len(temp_action_list) - 1].actionTime:
                    break
                # 没有函数响应的操作的处理
                while function_time > temp_action_list[action_list_index + 1].actionTime:
                    action_list_index = action_list_index + 1
                # 通过函数名匹配的方式过滤重名函数
                for function in temp_action_list[action_list_index].functionList:
                    if function.functionName == function_name:
                        break
                else:
                    temp_action_list[action_list_index].functionList.append(function)

                # 将函数运行可能产生的模块加入
                pattern = r'Dialog(\w+)Binding'
                match = re.search(pattern, package_name)
                if match:
                    dialogName = match.group(1) + 'Dialog'
                    transDialog(temp_state_list, action_list_index + 1, dialogName)

    def deleteState(self):
        index_to_remove = []
        # 删除非目标App节点
        for i, state in enumerate(self.stateList):
            if state.hierarchy['node']['@package'] != self.package or state.activityName == "NexusLauncherActivity":
                index_to_remove.append(i)
                if i < len(self.stateList) - 1:
                    self.stateList[i + 1].splitIndex = True

        # 删除因文本为空而无法匹配操作
        for i, state in enumerate(self.stateList[1:len(self.stateList)], start=1):
            if state.stateContentHash == self.stateList[i - 1].stateContentHash and self.actionList[i - 1].text == '':
                index_to_remove.append(i - 1)

        # 执行节点删除操作
        if index_to_remove.__len__() > 0:
            index_to_remove_set = setList(index_to_remove)
            for index in reversed(index_to_remove_set):
                self.stateList.pop(index)
                self.actionList.pop(index)

    # 把链整合成一张图
    def mergeState(self):
        # 首先获取所有界面的哈希值
        for i, state in enumerate(self.stateList):
            # self.stateList[i].stateHash = hash(state.activityName + ''.join(state.fragmentList) + state.dialogName)
            self.stateList[i].stateHash = hash(state.activityName + state.dialogName)
            self.stateList[i].getContentHash()

        # 完成删减节点操作
        self.deleteState()

        # 存放所有图节点，图内所有节点独一
        self.UTG.append(self.stateList[0])
        # 当前图节点的位置
        pre_state = self.stateList[0]
        for i, state in enumerate(self.stateList[1:len(self.stateList)], start=1):
            for j, node in enumerate(self.UTG):
                # 跳转到一个图上已有的节点而不是新节点，按照Activity，Fragment与Dialog三元组区分
                if node.stateHash == state.stateHash:
                    if pre_state is not self.UTG[j]:
                        # 在图上不同状态间的转换
                        transform = Edge(self.actionList[i - 1], self.UTG[j])
                    else:
                        # 在同一状态内的转换
                        transform = Edge(self.actionList[i - 1], None)
                    if not state.splitIndex:
                        pre_state.edgeList.append(transform)
                    pre_state = self.UTG[j]
                    self.stateList[i].visited = True
                    break
            # 跳转到一个新节点
            if not self.stateList[i].visited:
                self.UTG.append(self.stateList[i])
                transform = Edge(self.actionList[i - 1], self.stateList[i])
                pre_state.edgeList.append(transform)
                pre_state = self.stateList[i]

        for i, state in enumerate(self.stateList):
            self.stateList[i].visited = False


if __name__ == '__main__':
    package_name = "de.dennisguse.opentracks"
    model = Model(package_name)

    for index, state in enumerate(model.UTG):
        print("State: " + state.time, state.activityName, state.fragmentList, state.dialogName)
        print("Action: " + str(index) + ' ' + model.actionList[index].actionType, model.actionList[index].text)
