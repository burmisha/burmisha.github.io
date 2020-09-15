import logging
log = logging.getLogger(__file__)

import pprint
import re
import json

# def shortJson(data, maxLength):
#     # see also https://gist.github.com/socrateslee/d1c56f00000d9f1a9e1dabde5d0b7795
#     listItem = re.compile(r'(\S|[.\d]+),?')
#     lines = json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False).encode('utf8').split('\n')
#     resultLines = lines[0:1]
#     addedToPrevious = False
#     for line in lines[1:]:
#         stripped = line.strip()
#         # print '{!r}'.format([
#         #     stripped,
#         #     listItem.match(stripped),
#         #     len(resultLines[-1]) + len(stripped) < maxLength,
#         #     addedToPrevious,
#         # ])
#         if (
#             listItem.match(stripped) and len(resultLines[-1]) + len(stripped) < maxLength
#         ) or (
#             stripped in [']', '}', '],', '},'] and addedToPrevious
#         ) or (
#             stripped in ['[', '{']
#         ):
#             resultLines[-1] += ' ' + stripped
#             # print 'added'
#             addedToPrevious = True
#         else:
#             resultLines.append(line)
#             # print 'new'
#             addedToPrevious = False
#     result = '\n'.join(resultLines)
#     if json.loads(result) != data:
#         pprint.pprint(json.loads(result))
#         pprint.pprint(data)
#         raise RuntimeError()
#     return result


def shortJsonImpl(encodedJson, maxLength):
    # see also https://gist.github.com/socrateslee/d1c56f00000d9f1a9e1dabde5d0b7795
    listItem = re.compile(r'(\S|[.\d]+),?')
    lines = encodedJson.split('\n')
    resultLines = lines[0:1]
    addedToPrevious = False
    prevIndentLevel = None
    for line in lines[1:]:
        indentLevel = len(line) - len(line.lstrip(' '))
        stripped = line.strip()
        candidate = '{} {}'.format(resultLines[-1], stripped)
        if indentLevel >= prevIndentLevel and len(candidate) <= maxLength:
            resultLines[-1] = candidate
        else:
            resultLines.append(line)
            prevIndentLevel = indentLevel
    result = '\n'.join(resultLines)
    try:
        oldData = json.loads(encodedJson)
        newData = json.loads(result)
    except:
        pprint.pprint([oldData, newData])
        raise
    if oldData != newData:
        pprint.pprint([encodedJson, result])
        raise RuntimeError('Broken data')
    return result


def shortJson(data, maxLength):
    encodedJson = json.dumps(data, indent=4, separators=(',', ': '), ensure_ascii=False).encode('utf8')
    newLength = None
    while not newLength or newLength < prevLength:
        prevLength = len(encodedJson)
        encodedJson = shortJsonImpl(encodedJson, maxLength)
        newLength = len(encodedJson)
    return encodedJson

print shortJson([[["1108-burmisha-5426.jpg"]]], 100)
print shortJson([[["1108-burmisha-5426.jpg"] * 30]], 100)
print shortJson([[["1108-burmisha-5426.jpg"]] * 3], 100)
print shortJson([[[1, 2.0, 3]]], 100)
