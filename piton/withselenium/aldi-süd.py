from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import csv
from time import sleep
import re
import json
import pkgutil
from io import StringIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.common.action_chains import ActionChains


def load_csv_data(name):
    data = pkgutil.get_data('seleniumtest', 'data/{}'.format(name))
    sio = StringIO(data.decode('utf-8'))
    keys = next(sio).split(';')
    return [dict(zip(keys, line.strip().split(';'))) for line in sio.readlines()]


def day(index1, index2, info):
    try:
        day, hour = info[index1], info[index2]
        hour = re.split("</div>", hour)
        if hour[1] != "geschlossen":
            open, close = hour[1].split("-")
            return open, close
        else:
            return hour[1]
    except:
        pass


passed_zipcode = []
postcode = []
all_stores = []
zipcodes = []
de_cities = load_csv_data('de_cities.csv')
for city in de_cities:
    zips = city['PostalCode']
    zipcodes.append(zips)

with webdriver.Firefox(executable_path='/usr/local/bin/geckodriver') as driver:
    wait = WebDriverWait(driver, 10)
    original_window = driver.current_window_handle
    driver.get("https://www.aldi-sued.de/de/filialen.html")
    inputarea = driver.find_element_by_id("input__store_search")
    cookie = driver.find_element_by_class_name("js-privacy-accept")
    search = driver.find_element_by_css_selector("form#storeSearchForm button.btn-search-submit")
    cookie.click()
    sleep(5)

    with open('output.json', "r") as file:
        jsonfile = json.load(file)

    for zipcode in zipcodes:
        try:
            driver.execute_script("arguments[0].click();", inputarea)
            inputarea.send_keys(u'\ue009' + u'\ue003')
            inputarea.send_keys(u'\ue009' + u'\ue003')
            inputarea.send_keys(u'\ue009' + u'\ue003')
            inputarea.send_keys(u'\ue009' + u'\ue003')
            inputarea.send_keys(u'\ue009' + u'\ue003')
            inputarea.send_keys(u'\ue009' + u'\ue003')
            inputarea.send_keys(u'\ue009' + u'\ue003')

            inputarea.send_keys(zipcode)
            # search.click()
            driver.execute_script("arguments[0].click();", search)
            sleep(8)
            # search.click()
            driver.execute_script("arguments[0].click();", search)
            suggest = driver.find_element_by_css_selector("div.pac-container")
            # driver.execute_script("arguments[0].scrollIntoView();", suggest)
            driver.execute_script("arguments[0].scrollIntoView();", suggest)
            # ActionChains(driver).move_to_element(suggest).perform()
            # ActionChains(driver).click(suggest).perform()
            # move_to = ActionChains(driver).move_to_element(suggest)
            # move_to.perform()

            # actions = ActionChains(driver)
            # actions.move_to_element(suggest).perform()
            # sleep(1)

            items = driver.find_elements_by_class_name("dealer-item-content")
            for item in items:
                store = item.get_attribute('innerHTML')
                info = re.split(
                    '<strong>|</strong>|<span class="d-block dealer-address">|</span>|<span class="dealer-postal-code">|<span class="dealer-city">|daddr=|" target="_blank"',
                    store)
                name = info[1]
                address = info[4]
                zipcode = info[6]
                city = info[8]
                lat_lon = info[11].partition(",")
                lat = lat_lon[0]
                lon = lat_lon[2]
                saturday = day(25, 26, info)
                sunday = day(27, 28, info)
                monday = day(29, 30, info)
                tuesday = day(31, 32, info)
                wednesday = day(19, 20, info)
                thursday = day(21, 22, info)
                friday = day(23, 24, info)

                data = {
                    "Name": name,
                    "Address": address,
                    "City": city,
                    "GeoLocation": [lat, lon],
                    "PostCode": zipcode,
                    "Monday": [monday],
                    "Tuesday": [tuesday],
                    "Wednesday": [wednesday],
                    "Thursday": [thursday],
                    "Friday": [friday],
                    "Saturday": [saturday],
                    "Sunday": [sunday]
                }
                print(data)

                # sleep(5)
                # entry = json.dumps(data).decode("utf-8")
                if zipcode not in postcode:
                    postcode.append(zipcode)
                    all_stores.append(data)
                    with open("output.json", mode='r') as f:
                        jsonfile = json.load(f)
                    jsonfile.append(data)
                    with open("output.json", mode="w") as file:
                        json.dump(jsonfile, file)
                # sleep(5)

            sleep(3)

            # search.click()
            driver.execute_script("arguments[0].click();", search)
        except:
            passed_zipcode.append(zipcode)
    with open("passed_zipcode.json", mode="w") as passed_zipcodefile:
        json.dump(passed_zipcode, passed_zipcodefile)

    # print(all_stores)
    # with open("output.json", mode='w') as f:
    #     json.dump(all_stores, f)

# def tek_bi_urlden_data_ceken_fonksiyon(url):
#
#     return data
# exc = ThreadPoolExecutor(max_workers=ayni_anda_kac_request_yollasin)
# threads = []
# for url in urls:
#     threads.append(exc.submit(tek_bi_urlden_data_ceken_fonksiyon, url))
# for job in as_completed(threads):
#     data = job.result()
