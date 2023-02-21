import json
import re
import requests
import sys

itemList = []

def getId(name):
    for id in itemDB:
        if itemDB[id].startswith(name):
            return id
    return None

def getName(id):
    return itemDB[id]

def getCheapest(listings):
    cheapest = listings[0]
    for list in listings:
        if list['pricePerUnit'] < cheapest['pricePerUnit']:
            cheapest = list['pricePerUnit']
    return cheapest

def getAmount(itemId):
    for item in itemList:
        if item['id'] == itemId:
            return item['amount']
    return 0

with open('items.json') as itemsFile:
    itemDB = json.load(itemsFile)

itemRegx = re.compile(r'^(.+):\s(\d+)$')
sectionRegx = re.compile(r'((.|(?<=.)\n)+=+\n(.|(?<=\w)\n)+)')

### Parse the item list file
with open(sys.argv[1]) as shopListFile:
    shopList = shopListFile.read()
    sections = sectionRegx.findall(shopList)

    sectionName = 'unknown'

    for section in sections:
        section = section[0]
        items = section.splitlines()
        sectionName = items[0].strip()
        if sectionName == 'Furniture (With Dye)':
            continue
        for i in range(2, len(items)):
            match = itemRegx.match(items[i])
            item = {}
            item['item'] = match.group(1)
            item['id'] = getId(match.group(1))
            item['amount'] = int(match.group(2))
            itemList.append(item)

shoppingList = {}

### Get the list of items from the marketboard and filter the cheapest offers
for r in range(0, len(itemList), 100):
    itemIdList = ''
    for i in range(r, min(r+100, len(itemList))):
        itemIdList += itemList[i]['id'] + ','

    resJson = None

    res = requests.get('https://universalis.app/api/v2/Light/' + itemIdList)
    if(res.status_code == 200):
        resJson = res.json()
    else:
        print('HTTP Error: ' + res.status_code)
        continue

    for itemId in resJson['items']:
        chp = getCheapest(resJson['items'][itemId]['listings'])
        chpItem = {}
        chpItem['id'] = str(itemId)
        chpItem['name'] = getName(itemId)
        chpItem['amount'] = getAmount(itemId)
        chpItem['pricePerUnit'] = chp['pricePerUnit']
        if not chp['worldName'] in shoppingList:
            shoppingList[chp['worldName']] = []
        shoppingList[chp['worldName']].append(chpItem)

    if len(resJson['unresolvedItems']) > 0:
        shoppingList['unresolvedItems'] = []
        for itemId in resJson['unresolvedItems']:
            mitem = {}
            mitem['name'] = getName(str(itemId))
            mitem['id'] = str(itemId)
            mitem['pricePerUnit'] = 0
            shoppingList['unresolvedItems'].append(mitem)

### Print the list

subTotal = 0

for world in shoppingList:
    print(world + '\n===============')
    for item in shoppingList[world]:
        print(str(getAmount(item['id'])) + " " + item['name'] + "   (Unit price: " + str(item['pricePerUnit']) + ")")
        subTotal += item['pricePerUnit'] * getAmount(item['id'])
    print('\n')
print('subTotal: ' + str(subTotal) + ' gil')
