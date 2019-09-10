import sys
import glob
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.request import urlopen 
from bs4 import BeautifulSoup 
browser = webdriver.Chrome()
usernameStr = 'Sharon Hanna'
passwordStr = '0re02oo2'
browser.get('https://doh.arcabc.ca/user/login')
 
def uploadXML(filepath, browser, repo, num):
    import time
    import sys
    from urllib.request import urlopen    
    per1 = r'%3A'
    upldLnk=r'https://doh.arcabc.ca/islandora/object/' +repo+ per1 +num+ r'/datastream/MODS/replace#overlay-context=islandora/object/'
    browser.get(upldLnk)
    lockLnkTxt = "acquire the lock"
    lockWarning = len(browser.find_elements_by_partial_link_text(lockLnkTxt)) > 0
    if (lockWarning):
        acqLock = browser.find_element_by_partial_link_text(lockLnkTxt)
        acqLock.click()
        time.sleep(2)
        urlStr = 'https://doh.arcabc.ca/islandora/object/' + repo + per1 + num + '/manage/datastreams/locking/lock?destination=islandora%2Fobject%2F' + repo + per1 + num + '%2Fdatastream%2FMODS%2Freplace&'
        browser.get(urlStr)
        lockLnk = browser.find_element_by_id("edit-submit")
        lockLnk.click()

    subm = "//html/body/div[2]/div/div[2]/div/form/div/fieldset/div/input" #submit button xpath
    chooseFile = browser.find_element_by_css_selector("input#edit-file-upload")
    chooseFile.send_keys(filepath)

    time.sleep(2) #wait for file submission 
    try:
        browser.find_element_by_xpath(subm).click()
    except: # catch *all* exceptions
        print("Upload of " + repo + ":" + num + " failed.") 
        e = sys.exc_info()[0]
        print(e)
         
 
# fill in username and hit the next button
username = browser.find_element_by_id('edit-name')
username.send_keys(usernameStr)
password = browser.find_element_by_id('edit-pass')
password.send_keys(passwordStr)
signInButton = browser.find_element_by_id('edit-submit')
signInButton.click()

count = 0
for filename in glob.iglob(r'C:\\Users\sharo\Desktop\boun_oh_xml_only\**.xml', recursive=True):
    fnms = filename.split('\\')
    objIDpts = fnms[6].split("_")
    repo = objIDpts[0]
    num = objIDpts[1].split(".")[0]
    #print("repo " + repo + "; num " + num)
    uploadXML(filename, browser, repo, num)
    count += 1
print(str(count) + " XML files were uploaded.")