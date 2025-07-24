import os
import json

from model import Model
from model import State
from model import Action
from agent import zhipuLLM


# 测试用例类，以列表形式存储截取出的子图
class TestCase:
    def __init__(self):
        self.stateList = []
        self.actionList = []
        self.testAssert = ""

    def to_dict(self):
        """ 将testCase实例转换为字典 """
        return {
            'stateList': [state.to_dict() for state in self.stateList],
            'actionList': [action.to_dict() for action in self.actionList],
            'testAssert': self.testAssert
        }

    @staticmethod
    def save_to_jsonl(test_case, file_path):
        """ 将testCase实例保存为JSONL文件 """
        with open(file_path, 'a', encoding='utf-8') as file:
                print(test_case.testAssert)
                # print(test_case.stateList.__len__())
                # print(test_case.actionList.__len__())
                file.write(json.dumps(test_case.to_dict(), ensure_ascii=False) + '\n')


# 测试用例单个Node节点类，以树的形式存储测试用例集合
class TestCaseNode:
    def __init__(self, node_type, state, action, testAssert):
        self.node_type = node_type
        self.state = state
        self.action = action
        self.testAssert = testAssert
        self.visited = False

        self.childcnt = 0
        self.children = []
        self.parent = None

    @classmethod
    def from_dict(cls, data):
        typeStr, nodeData = data.split(' ', 1)
        typeStr = typeStr.upper()
        if 'STATE' in typeStr:
            node_type = 1
        elif 'ASSERT' in typeStr or 'Assert' in typeStr:
            node_type = 3
        elif 'TestCase' in nodeData:
            node_type = 0
        else:
            node_type = 2

        if node_type == 1:
            state = State.from_dict(nodeData)
            return cls(node_type, state, None, None)
        elif node_type == 2:
            action = Action.from_dict(data)
            return cls(node_type, None, action, None)
        elif node_type == 3:
            return cls(node_type, None, None, data)
        else:
            return cls(node_type, None, None, None)

    @staticmethod
    def load_from_jsonl(file_path):
        stack = []
        root = None
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                list = line.rstrip('\n').split('\t')
                index = [int(x) for x in list[0].split('.')]
                current_node = TestCaseNode.from_dict(list[1])
                while stack and stack[-1][0] >= len(index):
                    stack.pop()
                if stack:
                    stack[-1][1].childcnt += 1
                    stack[-1][1].children.append(current_node)
                    current_node.parent = stack[-1][1]

                    if current_node.node_type == 2:
                        current_node.state = stack[-1][1].state
                if not root:
                    root = current_node
                stack.append((len(index), current_node))
        return root

    def to_dict(self):
        """ 将testCaseNode实例转换为字典 """
        if self.node_type == 1:
            return {
                'node_type': self.node_type,
                'state': self.state.to_dict(),
                'child_cnt': self.childcnt
            }
        elif self.node_type == 2:
            return {
                'node_type': self.node_type,
                'action': self.action.to_dict(),
                'child_cnt': self.childcnt
            }
        elif self.node_type == 3:
            return {
                'node_type': self.node_type,
                'testAssert': self.testAssert,
                'child_cnt': self.childcnt
            }
        else:
            return {
                'node_type': self.node_type,
                'child_cnt': self.childcnt
            }

    def save_to_jsonl(self, file_path):
        """ 将测试用例集保存到JSONL文件 """
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(json.dumps(self.to_dict()) + '\n')

        for child in self.children:
            child.save_to_jsonl(file_path)


def splitTrace(state_list):
    state_list[0].splitIndex = True
    for index, state in enumerate(state_list[1:len(state_list)], start=1):
        if state.stateHash != state_list[index - 1].stateHash:
            state_list[index].splitIndex = True


def findBack(node: TestCaseNode, state: State, matchList: [], testCase: TestCase):
    while node.node_type != 0:
        if node.node_type == 1 and state.assertMatch(node.state.activityName):
            break
        if node.node_type == 2:
            testCase.stateList.pop(-1)
            testCase.actionList.pop(-1)
        node = node.parent
        matchList.pop(-1)
    if node.node_type == 0:
        return None
    return node


def findChild(state: State, action: Action, nextState: State, node: TestCaseNode):
    indexList = []
    equal_number = 0
    equal_index = -1
    for childidx in range(node.childcnt):
        if node.children[childidx].node_type == 3 and not node.children[childidx].visited:
            indexList.append(childidx)
        elif node.children[childidx].node_type == 2:
            eq = action.__eq__(node.children[childidx].action)
            if eq > equal_number:
                equal_number = eq
                equal_index = childidx
            else:
                child_node = node.children[childidx]
                if child_node.children[0].node_type == 3 and 'Assert' in child_node.children[0].testAssert:
                    parts = child_node.children[0].testAssert.split(' ', maxsplit=1)
                    if findStr(nextState.hierarchy, parts[1]) and equal_index == -1:
                        equal_number = 1
                        equal_index = childidx
        elif node.children[childidx].node_type == 1:
            eq = state.__eq__(node.children[childidx].state)
            if eq > equal_number:
                equal_number = eq
                equal_index = childidx
    if equal_index != -1:
        indexList.append(equal_index)
    # print('匹配index:' + str(indexList) + str(node.childcnt))
    return indexList


def findStr(hierarchy: dict, assertStr):
    res = [hierarchy]
    while res:
        currentNode = res.pop(0)
        if 'node' in currentNode:
            if type(currentNode['node']).__name__ == 'dict':
                res.append(currentNode['node'])
            else:
                for Node in currentNode['node']:
                    res.append(Node)
        if '@resource-id' in currentNode:
            if assertStr in currentNode['@resource-id'] or assertStr in currentNode['@content-desc'] or assertStr in \
                    currentNode['@text']:
                return True
    return False


def getData(testCase: TestCase, matchList: [], root: TestCaseNode):
    zhipu = zhipuLLM()
    with open('config.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        prompt1 = data['1']
        prompt2 = data['2']
    content = prompt1

    # 测试样例
    content_test_case = ''
    # node = root
    # for index in matchList:
    #     node = node.children[index]
    #     if node.node_type == 1:
    #         content_test_case += '[' + node.state.activityName + '] '
    #     if node.node_type == 2:
    #         content_test_case += '[' + node.action.actionType + ' ' + node.action.text + '] '
    content_test_case += '[' + testCase.testAssert.split()[1] + ']\n'
    content += content_test_case
    content += prompt2

    # 匹配的测试记录
    state = testCase.stateList[0]
    # content_state = '[起始界面]  ' + state.activityName + ' ' + ' '.join(state.fragmentList) + ' ' + state.dialogName + '\n'
    content_state = '[起始界面]  ' + state.activityName + ' ' +  state.dialogName + '\n'
    content_component = '[起始界面组件信息]  ' + state.getComponentsData().rstrip(',') + '\n'
    content += content_state + content_component

    for index, action in enumerate(testCase.actionList):
        actionType = action.actionType
        if 'CLICK' in actionType:
            viewText = action.text
            content_action = '[操作]' + 'actionType: ' + actionType + '; viewText: ' + viewText + '\n'
        else:
            content_action = '[操作]' + 'actionType: ' + actionType + '\n'
        content_function = ''
        for function in action.functionList:
            content_function += function.functionName + ','
        if content_function == '':
            content_action += '[操作响应函数信息] NULL \n'
        else:
            content_action += '[操作响应函数信息] ' + content_function.rstrip(',') + '\n'
        content += content_action

    state = testCase.stateList[-1]
    # content_state = '[终止界面]  ' + state.activityName + ' ' + ' '.join(state.fragmentList) + ' ' + state.dialogName + '\n'
    content_state = '[终止界面]  ' + state.activityName + ' ' + state.dialogName + '\n'
    content_component = '[终止界面组件信息]  ' + state.getComponentsData().rstrip(',') + '\n'
    content += content_state + content_component

    print(content)

    zhipu.addUserMessage(content)
    result = zhipu.getResponse()
    print(result)

    if 'True' == result:
        return True
    else:
        return False


def isAssert(testCase: TestCase, matchList: [], root: TestCaseNode):
    if 'ASSERT1' in testCase.testAssert:
        test_case_state_assert = testCase.testAssert.split(' ', maxsplit=1)[1]
        return testCase.stateList[-1].assertMatch(test_case_state_assert)
    elif 'ASSERT2in' in testCase.testAssert:
        parts = testCase.testAssert.split(' ', maxsplit=1)
        return findStr(testCase.stateList[-1].hierarchy, parts[1])
    elif 'ASSERT2notin' in testCase.testAssert:
        parts = testCase.testAssert.split(' ', maxsplit=1)
        return not findStr(testCase.stateList[-1].hierarchy, parts[1])
    elif 'ASSERT3' in testCase.testAssert:
        return getData(testCase, matchList, root)


# 获取配对子图阶段的函数
def matchTestCase(state_list: [], action_list: [], index: int, root: TestCaseNode):
    # 在这个函数中完成调用Assert判断的操作，函数返回匹配到的TestCase的list
    testCaseList = []
    # 记录匹配到的测试记录子图/子集
    testCase = TestCase()
    # 记录匹配到的用例的编号
    matchList = []
    historyMatch = 0

    node = root
    state = state_list[index]
    state.splitIndex = False
    while index < state_list.__len__() - 1:
        state = state_list[index]
        if state.splitIndex and matchList.__len__() == historyMatch:
            return testCaseList
        else:
            historyMatch = len(matchList)

        index_list = findChild(state, action_list[index], state_list[index + 1], node)
        if index_list.__len__() > 0:
            for childidx in index_list:
                if node.children[childidx].node_type == 3:
                    testCase.stateList.append(state)
                    testCase.testAssert = node.children[childidx].testAssert
                    if isAssert(testCase, matchList, root):
                        # 加入testCaseList并保存文件
                        testCaseList.append(testCase)
                        path = os.path.join('result', package_name, package_name + '.a1.jsonl')
                        TestCase.save_to_jsonl(testCase, path)

                        node.children[childidx].visited = True
                        testCase.stateList.pop(-1)
                        if node.childcnt == 1:
                            node = findBack(node, state, matchList, testCase)
                            if node is None:
                                return testCaseList
                            else:
                                continue
                    else:
                        return testCaseList
                elif node.children[childidx].node_type == 2:
                    testCase.stateList.append(state)
                    testCase.actionList.append(action_list[index])
                    index += 1
                    node = node.children[childidx]
                    matchList.append(childidx)
                elif node.children[childidx].node_type == 1:
                    node = node.children[childidx]
                    matchList.append(childidx)
        else:
            # 没找到的话的递进逻辑
            index += 1
    return testCaseList


def getResult(package_name):
    path = os.path.join('result', package_name, package_name + '.a1.jsonl')
    with open(path, 'w', encoding='utf-8') as file:
        print("Old Result Deleted")
    model = Model(package_name)
    splitTrace(model.stateList)

    # 读取测试用例集：Clock / Notes / Music
    path = os.path.join('result', package_name, 'testCase.txt')
    root = TestCaseNode.load_from_jsonl(path)

    testCaseList = []
    number = 0
    for index, state in enumerate(model.stateList):
        if state.splitIndex:
            # if number > 10:
            #     break
            print("=" *  10 + "BEGIN " + str(number) + "=" * 10)
            number = number + 1
            testCaseList += matchTestCase(model.stateList, model.actionList, index, root)

    # 遍历所有存在即可以的测试样例
    queue = [root]
    while queue:
        node = queue.pop(0)

        # 访问当前节点
        if node.node_type == 3 and 'ASSERT1in' in node.testAssert and not node.visited:
            for state in model.UTG:
                if state.assertMatch(node.testAssert.split(' ', maxsplit=1)[1]):
                    testCase = TestCase()
                    testCase.testAssert = node.testAssert
                    testCaseList.append(testCase)
                    path = os.path.join('result', package_name, package_name + '.a1.jsonl')
                    TestCase.save_to_jsonl(testCase, path)
                    break

        # 标记为已访问
        node.visited = True

        # 将子节点加入队列
        for child in node.children:
            if not child.visited:
                queue.append(child)

    print('testCaseLen: ' + str(testCaseList.__len__()))
    return testCaseList


if __name__ == '__main__':
    """
    org.fossify.clock
    ac.mdiq.podcini.R
    org.fossify.notes
    de.dennisguse.opentracks
    ml.docilealligator.infinityforreddit
    """
    package_name = "ac.mdiq.podcini.R"
    getResult(package_name)
