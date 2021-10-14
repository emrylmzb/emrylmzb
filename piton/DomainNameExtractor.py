import re


# def domain_name(url):
#     info = re.split('//|www.',url)
#     result = info[1].split(".com")
def remove_unwanted(list, string):
    try:
        list.remove(string)
    except:
        pass
    return list


def domain_name(url):
    if "https://" or "http://" in url:
        url = url.split("//")
        remove_unwanted(url, "https:")
        remove_unwanted(url, "http:")

    info = url[0].split(".")
    remove_unwanted(info, "www")
    print(info[0])


