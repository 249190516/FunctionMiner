# # 包含有Merge的getComponentsData
# def getMergedComponents(jsonData: dict):
#     stack = [jsonData]
#     res = []
#     # 主循环
#     while stack:
#         currentNode = stack.pop(0)
#         # 节点为组件节点，判断是否是目标应用组件
#         if '@resource-id' in currentNode:
#             # 节点可点击且有子节点，尝试 Merge
#             if currentNode['@clickable'] == 'true' and 'node' in currentNode:
#                 currentNode['@clickable'] = 'false'
#                 mergeStack = [currentNode]
#                 mergeStr = ''
#                 mergedList = []
#                 # merge循环
#                 while mergeStack:
#                     mergedNode = mergeStack.pop(0)
#
#                     if mergedNode['@clickable'] != 'true':
#                         size = len(mergeStr)
#                         if mergedNode['@text']:
#                             mergeStr += mergedNode['@text']
#                         elif mergedNode['@content-desc']:
#                             mergeStr += mergedNode['@content-desc']
#                         if size != len(mergeStr):
#                             # 间隔符号
#                             mergeStr += ' '
#                             mergedList.append(mergedNode)
#                         if 'node' in mergedNode:
#                             if type(mergedNode['node']).__name__ == 'dict':
#                                 mergeStack.insert(0, mergedNode['node'])
#                             else:
#                                 for node in mergedNode['node']:
#                                     mergeStack.insert(0, node)
#                     else:
#                         while mergeStack:
#                             tempNode = mergeStack.pop(0)
#                             stack.insert(0, tempNode)
#                         while mergedList:
#                             tempNode = mergedList.pop(0)
#                             res.append(tempNode)
#                         stack.insert(0, mergedNode)
#                         mergeStr = 'Error: Ano'
#
#                 if mergeStr != 'Error: Ano':
#                     currentNode['@text'] = mergeStr
#                     res.append(currentNode)
#                 continue
#             else:
#                 res.append(currentNode)
#
#         if 'node' in currentNode:
#             if type(currentNode['node']).__name__ == 'dict':
#                 stack.insert(0, currentNode['node'])
#             else:
#                 for Node in currentNode['node']:
#                     stack.insert(0, Node)
#     return res
#
#
# def getComponentsData(jsonData: dict):
#     res = getMergedComponents(jsonData)
#     components_str = ''
#
#     for currentNode in res:
#         if '@resource-id' in currentNode:
#             if 0 < len(currentNode['@content-desc']) < 10:
#                 components_str += "{},".format(currentNode['@content-desc'])
#                 continue
#             elif 0 < len(currentNode['@text']) < 10:
#                 components_str += "{},".format(currentNode['@text'])
#                 continue
#             elif 0 < len(currentNode['@resource-id']) < 20:
#                 components_str += currentNode['@resource-id'].split('/')
#     return components_str

# 获取界面信息的XML文件部分的废弃代码（更健壮，但我不喜欢）
# for file_name in os.listdir(self.data_trace):
#     if file_name.endswith('.xml'):
#         file_time = file_name[:-4]  # 剔除文件扩展名部分；文件的时间作为名称
#         file_time = file_time.replace('-', ':')
#         if file_time == action.actionTime:
#             file_path = os.path.join(self.data_trace, file_name)
#             with open(file_path, 'r', encoding='utf-8') as file:
#                 xml_data = file.read()
#                 hierarchy = xmltodict.parse(xml_data)
#             state = State(hierarchy, activity_name, fragment_list)
#             self.state_list.append(state)
