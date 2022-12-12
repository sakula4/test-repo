import json
import sys
import os
import ast


def getEnabledKeysFromStack(stack: list, enabledKeyList: list):
    enabled_stack = []
    for stackKey in stack:
        if stackKey in enabledKeyList:
            enabled_stack.append(stackKey)
    return enabled_stack


metadata_stack = ast.literal_eval(os.getenv('metadata_stack'))
datadog_stack = ast.literal_eval(os.getenv('datadog_stack'))
baseline_stack = ast.literal_eval(os.getenv('baseline_stack'))
networking_stack = ast.literal_eval(os.getenv('networking_stack'))
tableau_stack = ast.literal_eval(os.getenv('tableau_stack'))
abc_stack = ast.literal_eval(os.getenv('abc_stack'))
datalake_stack = ast.literal_eval(os.getenv('datalake_stack'))

fileName = sys.argv[1]

f = open(fileName)
enabledKeys = []
enabledMap = {}
data = json.load(f)

localData = data['locals']
for x in localData:
    keys = x.keys()
    for key in keys:
        internalData = localData[0][key]
        if type(internalData) is dict:
            internalKeys = internalData.keys()
            for internalKey in internalKeys:
                if (internalKey == 'enabled' and internalData.get('enabled')):
                    enabledKeys.append(key)
                    enabledMap.setdefault(key, internalData.get('path'))


# metadata_layers = list(set(metadata_stack).intersection(enabledKeys))
# datadog_layers = list(set(datadog_stack).intersection(enabledKeys))
# baseline_layers = list(set(baseline_stack).intersection(enabledKeys))
# networking_layers = list(set(networking_stack).intersection(enabledKeys))
# tableau_layers = list(set(tableau_stack).intersection(enabledKeys))
# abc_layers = list(set(abc_stack).intersection(enabledKeys))
# datalake_layers = list(set(datalake_stack).intersection(enabledKeys))


metadata_layers = getEnabledKeysFromStack(metadata_stack, enabledKeys)
datadog_layers = getEnabledKeysFromStack(datadog_stack, enabledKeys)
baseline_layers = getEnabledKeysFromStack(baseline_stack, enabledKeys)
networking_layers = getEnabledKeysFromStack(networking_stack, enabledKeys)
tableau_layers = getEnabledKeysFromStack(tableau_stack, enabledKeys)
abc_layers = getEnabledKeysFromStack(abc_stack, enabledKeys)
datalake_layers = getEnabledKeysFromStack(datalake_stack, enabledKeys)

print("filepath_map=", enabledMap)
print("metadata_layers=", metadata_layers)
print("datadog_layers=", datadog_layers)
print("baseline_layers=", baseline_layers)
print("networking_layers=", networking_layers)
print("tableau_layers=", tableau_layers)
print("abc_layers=", abc_layers)
print("datalake_layers=", datalake_layers)
