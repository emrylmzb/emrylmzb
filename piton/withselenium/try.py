import json


with open('output.json', "r") as file:
    jsonfile = json.load(file)
# items = []
# n = 0
# while n < 8:
#     data = {
#         "Name": "name",
#         "Address": "address",
#         "City": "city",
#         "GeoLocation": ["lat", "lon"],
#         "Monday": ["moopen", "moclose"],
#         "Tuesday": ["tuopen", "tuclose"],
#         "Wednesday": ["weopen", "weclose"],
#         "Thursday": ["thopen", "thclose"],
#         "Friday": ["fropen", "frclose"],
#         "Saturday": ["saopen", "saclose"],
#         "Sunday": ["suhour"[1]]
#     }
#     person_dict = json.dumps(data).decode("utf-8")
#
# print(items)
