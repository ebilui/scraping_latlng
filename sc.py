from encodings import utf_8
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome import service as fs
import re
import csv
import pandas as pd
import glob
from difflib import SequenceMatcher
# import socks, socket
import subprocess

start = time.perf_counter()
print('start scraping')

def restart_tor():
    # socks.set_default_proxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9050)
    # socket.socket = socks.socksocket
    # subprocess.run(["killall -HUP tor"], shell=True)
    subprocess.run(["brew services restart tor"], shell=True)
    time.sleep(5)

class UrlHasChanged:
    def __init__(self, old_url):
        self.old_url = old_url

    def __call__(self, driver):
        print(driver.current_url)
        return (driver.current_url != self.old_url) or ('/@' in driver.current_url)


options = Options()
# UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
# options.add_argument('--headless')
options.add_argument('--disable-gpu')
# options.add_argument('--disable-extensions') 
# options.add_argument('--proxy-bypass-list=*') 
options.add_argument('--proxy-server=socks5://127.0.0.1:9150')
# options.add_argument('--lang=ja') 
options.add_argument("--log-level=3")
# options.add_experimental_option("excludeSwitches", ["enable-automation"])
# options.add_argument('--disable-dev-shm-usage')
# options.add_argument('--user-agent=' + UA)
options.page_load_strategy = 'eager'
# options.add_argument('--blink-settings=imagesEnabled=false')

chrome_service = fs.Service(executable_path="./chromedriver")

df = pd.read_csv("./バス停データ/人力データ収集 - 緯度経度、バス停名.csv", header=None)
k = 3149  # 1DataFrameあたりの行数
dfs = [df.loc[i:i+k-1, :] for i in range(0, len(df), k)]
for i, df_i in enumerate(dfs):
    fname = "./split_3data/" + str(i) + ".csv"
    df_i.to_csv(fname)

header_row = ['必要なバス停名', '取得バス停名', '緯度', '経度']
with open('map.csv', 'w', newline="")as f:
    writer = csv.writer(f)
    writer.writerow(header_row)
f.close()

i = 0
files = glob.glob("./split_3data/*")
for file in files:
    with open(file) as f:
        header = next(csv.reader(f))
        reader = csv.reader(f)
        for row in reader:
            if (i == 0):
                if 'driver' in locals():
                    driver.close()
                restart_tor()
                driver = webdriver.Chrome(service=chrome_service, options=options)
                print('-------------------------------------------------')
                print('my ip address')
                subprocess.run(["curl -sL --socks5 127.0.0.1:9050 https://icanhazip.com/"], shell=True)
                print('-------------------------------------------------')
            lat_lng = row[1]
            bas_station = row[2]
            url = "https://www.google.co.jp/maps/@{0},18z".format(lat_lng)

            print('opening chrome...')

            driver.get(url)
            if 'consent.google.co.jp' in driver.current_url:
                selector = '#yDmH0d > c-wiz > div > div > div > div.NIoIEf > div.G4njw > div.AIC7ge > div.CxJub > div.VtwTSb > form:nth-child(2) > div > div > button'
                element = WebDriverWait(driver, 60).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                driver.find_element(By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]/div/div/button').click()
                
            selector = '#passive-assist > div > div.J43RCf > div > div'
            element = WebDriverWait(driver, 100).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
            )

            if (i == 0):
                time.sleep(4)

            chrome_open_time = time.perf_counter() - start
            print('complete open chrome : ' + str(chrome_open_time))
            # get_data()

            print('getting data...')

            search_bar = driver.find_element(By.ID, "searchboxinput")
            search_bar.send_keys('バス停')
            search_button = driver.find_element(By.XPATH, "//*[@id='searchbox-searchbutton']")
            search_button.click()
            selector = '#QA0Szd > div > div > div.w6VYqd > div.bJzME.tTVLSc > div > div.e07Vkf.kA9KIf > div > div > div.m6QErb.DxyBCb.kA9KIf.dS8AEf.ecceSd > div.m6QErb.DxyBCb.kA9KIf.dS8AEf.ecceSd > div:nth-child(1)'
            element = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
            )

            soup = BeautifulSoup(driver.page_source, "html.parser")
            a_tags = soup.find_all("a")
            matches = []
            for a_tag in a_tags:
                if a_tag.has_attr('aria-label'):
                    label = a_tag['aria-label']
                    replace_label = ''
                    if ('（バス）' in label):
                        replace_label = label.replace('（バス）', '')
                    ratio = SequenceMatcher(None, bas_station, label if replace_label=='' else replace_label)
                    print(bas_station + ' | ' + label)
                    print(ratio.ratio())
                    print('-------------------------------------------------')
                    if (ratio.ratio() > 0.7):
                        matches.append(label)
            matches = list(set(matches))

            replace = []
            for match in matches:
                match_a_tags = soup.find_all('a', attrs={ 'aria-label': match })
                for match_a_tag in match_a_tags:
                    if ('のウェブサイトにアクセス' in match_a_tag):
                        continue
                    match_href = match_a_tag.get('href')
                    replace.append(str(match_href).replace('amp;', ''))
                
            get_data_time = 0
            with open('map.csv', 'a', newline="")as f:
                writer = csv.writer(f)
                i += 1
                if (i == 3):
                    i = 0
                if (replace == []):
                    lat_lng = lat_lng.split(',')
                    writer.writerow([bas_station, '取得不可', lat_lng[0], lat_lng[1]])
                else:
                    for url in replace:
                        driver.get(url)
                        current_url = driver.current_url
                        WebDriverWait(driver, 10).until(UrlHasChanged(current_url))
                        soup = BeautifulSoup(driver.page_source, "html.parser")
                        h1 = soup.find('h1', class_='fontHeadlineLarge')
                        label = h1.get_text()

                        cur_url = driver.current_url

                        if get_data_time == 0:
                            get_data_time = time.perf_counter() - chrome_open_time
                            print('got lat,lng : ' + str(get_data_time))

                        # print('get url : ' + cur_url)
                        p = r'@(.*)'
                        after_latlng = re.search(p, cur_url)
                        lat = after_latlng.group(1).rsplit(',', 2)[0]
                        lng = after_latlng.group(1).rsplit(',', 2)[1]
                        print('out put to csv file...')
                        writer.writerow([bas_station, label, lat, lng])
            f.close()
    f.close()
driver.close()
driver.quit()

print('complete')
print('total : ' + str(time.perf_counter()))


# set_options()
# files = glob.glob("./split_3data/")
# for file in files:
#     open_url(file)
#     open_url()