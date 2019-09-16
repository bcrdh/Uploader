import glob
import os
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from robobrowser import RoboBrowser
import sys

"""
The session that will be used by
all browser instances to access the
collections. Set in sign_in()
"""
global_session = None
# The number of files successfully uploaded
count = 0
# The lock to increment count safely (thread safety)
countLock = threading.Lock()
# The base URL of the DOH Arca website
base_url = 'https://doh.arcabc.ca'
# The list of futures from the threadpool
futures = []


def sign_in(username, password):
    """
    Signs into the DOH website and sets the global session
    to allow other browser instances to access the cookies
    :param username: the username to login with
    :param password: the password to login with
    """
    # Create Non-JS browser
    browser = RoboBrowser(parser='html.parser')
    # Open login page
    browser.open('https://doh.arcabc.ca/user/login')
    # Get the login form
    form = browser.get_form(id='user-login')
    # Set the username & password
    form['name'].value = username
    form['pass'].value = password
    # Submit the form
    browser.submit_form(form)
    # Set the global session
    global global_session
    global_session = browser.session


def get_lock_link(links):
    """
    Gets the link that allows to lock a
    collection object in order to modify it
    :param links: the list of links on the current page of the browser
    :return: the href of the correct link to acquire the lock
    """
    for link in links:
        if link.text == 'acquire the lock':
            return link['href']


def get_unlock_link(links):
    """
    Gets the link that allows to unlock a
    collection object in order to let others to modify it again
    :param links: the list of links on the current page of the browser
    :return: the href of the correct link to release the lock
    """
    for link in links:
        if link.text == 'release':
            return link['href']


def acquire_lock(browser, manage_url):
    """
    Acquires the lock of a collection object in order to modify it
    :param browser: the browser that is currently browsing the collection object
    :param manage_url: the management url of the object to acquire the lock of
    :return: a boolean indicating if the acquisition was successful
    """
    try:
        browser.open(manage_url)
        lock_link = get_lock_link(browser.get_links())

        if lock_link is not None:
            global base_url
            # Open the link to lock
            browser.open(base_url + lock_link)
            # Find the form by class and submit it
            browser.submit_form(browser.get_form(class_='confirmation'))
            # Success
            return True
        # Failed to acquire lock because someone else
        # has locked this object
        else:
            return False
    # Any error indicates failure
    except Exception as e:
        return False


def release_lock(browser, manage_url):
    """
    Releases the lock of a collection object in order to let others
    modify it.
    :param browser: the browser that is currently browsing the collection object
    :param manage_url: the management url of the object to release the lock of
    """
    try:
        browser.open(manage_url)
        unlock_link = get_unlock_link(browser.get_links())
        # if unlock_link is None, then
        # the object is not locked anyways
        if unlock_link is not None:
            global base_url
            browser.open(base_url + unlock_link)
            browser.submit_form(browser.get_form(class_='confirmation'))
    # No return for this as we don't really care
    # if we released the lock since it automatically
    # releases in 30 minutes.
    except Exception as e:
        pass


def upload_xml(file, repo, num):
    """
    Uploads the MODS XML file to the appropriate object given the
    repository namespace and number of the specific object.
    :param file: the path of the MODS XML file to reingest
    :param repo: the repository namespace derived from the file name
    :param num: the number of the object derived from the file name
    :return: None
    """
    global base_url
    # URL for managing the object
    manage_url = 'https://doh.arcabc.ca/islandora/object/' + repo + '%3A' + num + '/datastream/MODS/replace'
    # Create a new browser instance
    browser = RoboBrowser(session=global_session, parser='html.parser')
    try:
        # Acquire the lock for the object
        if acquire_lock(browser, manage_url):
            # Go to the MODS replace page
            browser.open('https://doh.arcabc.ca/islandora/object/' + repo + '%3A' + num + '/datastream/MODS/replace')
            # Get the upload file form
            form = browser.get_form(id='islandora-datastream-version-replace-form')
            # Set the file to upload
            form['files[file]'].value = open(file, 'r')
            # This submit submits the form
            browser.submit_form(form, submit=form['op'])
            print('Uploaded ' + file)
            # Increment count (safely)
            countLock.acquire()
            global count
            count = count + 1
            countLock.release()
            # Release the lock
            release_lock(browser, manage_url)
        else:
            print('Failed to update object: ' + file + ' as the lock could not be acquired.')
    except Exception as e:
        print('Failed to update object: ' + file)
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        ffname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, ffname, exc_tb.tb_lineno)
        # Release the lock
        release_lock(browser, manage_url)

    return None


sign_in('Sharon Hanna', '0re02oo2')
"""
10 workers so the website is not overloaded
with excessive uploading / parsing of the XML files
This might be able to go higher, we just have to experiment
"""
with ThreadPoolExecutor(max_workers=10) as executor:
    file_list = set()
    for filename in glob.iglob(
            'C:\\Users\\ragha\\code\\python\\DOH_uploader\\UpdatedXML\\**\\*.xml', recursive=True):
        file_list.add(filename)

    for filename in file_list:
        fnms = filename.split('\\')
        objIDpts = fnms[-1].split("_")
        repository = objIDpts[0]
        number = objIDpts[1].split(".")[0]
        futures.append(executor.submit(upload_xml, filename, repository, number))

    for future in futures:
        future.result()

print(count)
print('Finished! Uploaded ' + str(count) + ' files.')
