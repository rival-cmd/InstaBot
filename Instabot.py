import sys, os, time, configparser, logging, re
import GUI
from bs4 import BeautifulSoup as BS
from threading import Thread, RLock
from queue import Queue
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException, ElementClickInterceptedException, TimeoutException



class InstagramBot():
    """Selenium Automated Bot For Instagram\n
    Varibles Loaded from config.ini\n 
    Account Credential, File Paths, Hashtag to Parse"""

    def __init__(self):

        #Instagram Account Login Bool
        self.logged_in = False
        #Thread Lock Variable
        self.lock = RLock()
        self.que = Queue()

        #Import Config.ini and Configure
        cwd = os.getcwd()
        platform = sys.platform
        if platform == 'win32' or 'cygwin':
            config_file = (cwd + '\\config.ini').replace('\\', '\\\\')
            self.xmlfile = (cwd + '\\XML.txt').replace('\\', '\\\\')
            CHROME_USERDATA = (cwd + '\\chromeuserdata').replace('\\', '\\\\')
            CHROMEDRIVER_PATH = (cwd + "\\chromedriver.exe").replace('\\', '\\\\')
        else:
            config_file = (cwd + '/config.ini')
            self.xmlfile = (cwd + '/XML.txt')
            CHROME_USERDATA = (cwd + '/chromeuserdata')
            CHROMEDRIVER_PATH = (cwd + "/chromedriver.exe")

        try:
            config = configparser.ConfigParser()
            config.read(config_file)
        except configparser.Error:
            print('''config.ini Error, Please Check File Paths \n 
                    Make sure Chromedriver.exe is in the Current Working Directory and\n
                    Chromedriver and Google Chrome are at compatable versions.''')

        #Instagram Account Username and Password
        self.username = config['IG_AUTH']['USERNAME']
        self.password = config['IG_AUTH']['PASSWORD']

        #Logger for Instagram Account Actions- Likes, Follows, ect
        logging.basicConfig(level=logging.INFO,
                                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                                            datefmt='%m-%d %H:%M',
                                            filename=config['LOGS']['INSTAGRAM'],
                                            filemode='w')
        self.logger=logging.getLogger(self.username)
        

        #URL Variables
        self.base_url = config['IG_URLS']['BASE']
        self.login_url = config['IG_URLS']['LOGIN']
        self.nav_url = config['IG_URLS']['NAV_USER']
        self.tag_url = config['IG_URLS']['SEARCH_TAGS']

        #Instagram Variables
        self.tags = config['TAGS']['TAGS_TO_LIKE'].split(',')
        self.max_likes = int(config['VARS']['MAX_LIKES'])
        self.MINIMUM_NUMBER_OF_LIKES =  int(config['VARS']['MINIMUM_NUMBER_OF_LIKES'])
        self.liked_pictures = 0
        self.new_followers = 0

        #Selenium Driver
        options = webdriver.ChromeOptions()
        options.add_argument('user-data-dir={}'.format(CHROME_USERDATA))
        options.add_argument('--incognito')
#       options.add_argument('--headless')
        self.driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                                            service_log_path=config['LOGS']['CHROME'],
                                            options=options)

        #Populate Queue with Tags from config.ini
        for item in self.tags:
            self.que.put(item)



    def login(self):
        """Uses credentials from config.ini to log into instagram: 3 Attempts"""
        self.logger.info('Success')
        connection_attempts = 0
        while connection_attempts < 3:
            try:
                self.driver.get(self.login_url)
                WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, '//div[4]//button[1]')))
                #Submit Login Credentials
                self.driver.find_element_by_name('username').send_keys(self.username)
                self.driver.find_element_by_name('password').send_keys(self.password)
                time.sleep(.5)
                # Click Login Button
                self.driver.find_element_by_xpath('//button[@type=\"submit\"]').click()
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH,'//input[@placeholder="Search"]')))
                #Login Success, Print, Flip Bool, Return Thread
                print("Login Success \n Username: {}\n Password: {}".format(self.username, self.password))
                self.logged_in = True
            #Try Block Exception Handling
            except NoSuchElementException:
                connection_attempts += 1
                print('XPath Parsing Error')
            except Exception as ex:
                    connection_attempts += 1
                    print(f'Attempt #{connection_attempts}.')
                    print(f'Error connecting to {self.login_url}.')
                    print(ex)
                    time.sleep(2)
            return False


    def logged(self):
        """Return Bool of Chromewebdriver Instagram Login\n
        Bool is Flipped at end of login function"""
        return self.logged_in


    def update(self):
        """Update GUI with number of Posts Liked This Session"""
        return (self.liked_pictures,self.new_followers)


    def queue(self):
        """Return Tag or False if empty"""
        que = self.que.get()
        if que != None:
            return que
        else:
            return False


    def quit(self):
        """Close Web Browser"""
        self.driver.quit()


    def scroll_down(self):
        """Scroll Down Webpage"""
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(.5)
        except:
            print('Failed Scroll Down Script')
        return


    def nav_user(self, user=None):
        """Pass in single argument: instagram username handle \n""" 
        self.driver.get('{}/{}/'.format(self.base_url, user))
        return


    def follow_user(self, user=None):
        """ Pass in single argument: instagram username handle """
        #Naviagte to users page
        self.driver.get(self.nav_url.format(user))
        try:
            WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Follow')]"))).click()
            time.sleep(.5)
            print("Now Following: {}".format(user))
            self.logger.info("Now Following: {}".format(user))
            self.new_followers += 1
        except NoSuchElementException:
            print('Error Trying to Follow {}   -Follow Button Not Found'.format(user))
            self.logger.info('Error Trying to Follow {}   -Follow Button Not Found'.format(user))
            return False
        return True


    def unfollow_user(self, user=None):
        """Pass in single argument: instagram username handle"""
        try:
            #Click Unfollow and Confirm Messagebox
            WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Following")]'))).click()
            WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Unfollow")]'))).click()
            print("Now Not Following: {}".format(user))
            self.logger.info("Now Not Following: {}".format(user))
        except NoSuchElementException:
            print('Error Trying to Un-Follow {}   -Un-Follow Button Not Found'.format(user))
            self.logger.info('Error Trying to Un-Follow {}   -Un-Follow Button Not Found'.format(user))
            return False
        return True


    def like_hearts(self, url=None):
        """Click glyphsSpriteHeart on a given page if likes >= MINIMUM_NUMBER_OF_LIKES from config.ini """

        #Like Buttons
        heart = (By.XPATH, "//button/span[contains(@class,'glyphsSpriteHeart__outline__24__grey_9 u-__7')]")
        # filled_heart = (By.XPATH, "//span[contains(@class,'glyphsSpriteHeart__filled__24__red_5 u-__7')]")

        # XPATH for scraping number of likes the media has: First:Pictures / Second:Videos
        xpath = [(By.XPATH, '//section[2]/div/div/button/span'),
            (By.XPATH,  '//section[2]/div/span/span')] 

        try:
            self.logger.info('Starting URL Crawl For {}'.format(url))
            self.driver.get(url)

            #Find the Number of Likes the media.
            for by, value in xpath:
                try:
                    element = self.driver.find_element(by, value)
                    text = element.text.replace(',',"")
                    #text = elem_var.replace(',',"")
                    numbers = re.compile(r'[1-9]\d*|0\d+')
                    likes = re.match(numbers,text)

                    #If Likes >= config.ini [VARS][MINIUMUM_NUMBER_OF_LIKES] Click Like Button
                    if likes:
                        if int(likes.group(0)) >= self.MINIMUM_NUMBER_OF_LIKES:
                            try:
                                WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable(heart)).click()
                                print('\nLiked Picture at: {} \nLikes = {}\n'.format(url, likes.group(0)))
                                self.logger.info('\nLiked Picture at: {} \tLikes = {}\n'.format(url, likes.group(0)))
                                self.liked_pictures += 1
                                time.sleep(.5)
                            except NoSuchElementException:
                                self.logger.info('Selenium Driver Failed to Clck Like Button at {}'.format(url))
                                pass
                            except Exception as e:
                                self.logger.info('Error: {}'.format(e))
                except NoSuchElementException:
                    pass
            return True
        except StaleElementReferenceException as SE:
            print('Failed to like picture: No Longer Attached to the DOM')
            print(SE)
        except ElementClickInterceptedException as ECI:
            print('Failed to like picture: Overlaying Element')
            print(ECI)
        except Exception as Ex:
            print('Selenium Page Error at {}'.format(url))
            print(Ex)
            


    def spider_scrawl(self, tag=None):
        """Selenium + BS4 Spider\n
        Spider TAGS_TO_LIKE from config.ini file\n
        Likes all pictures with more than 100 likes from each hashtag\n
        Once queue is empty, return to GUI"""

        links = []
        href = []

        #Get Webpage
        self.driver.get(self.tag_url.format(tag))
        WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, '//header')))
        self.scroll_down()
        time.sleep(2)
        try:        #Get Page HTML Source, use Regex to match the URL ShortCode
            text = self.driver.page_source
            soup = BS(text, 'html.parser')
            html = soup.find_all('a', href=True)
            pattern = re.compile(r'\/p\/.{11,12}\/')
            for tag in html:
                match  = re.match(pattern, tag.attrs['href'])
                if match != None:
                    href.append(tag.attrs['href'])

        #Debug File, may be used to crawl for usernames in later loop
            with open(self.xmlfile, "w") as file:
                for item in href:
                    file.write(item)
                    file.write('\n')

            #Create FQDN for each shortcode, and 
            for item in href:
                    link = (self.base_url.format(item))
                    if link not in links:
                        links.append(link)

            self.logger.info('-----{}-----\n\t\t Found Following Links:\n{}'.format(self.driver.current_url, tuple(links)))
            
            #Open each URL SHORTCODE, find the number of likes and like post if likes >= MINIMUM_NUMBER_OF_LIKES from config.ini
            for item in links:
                self.like_hearts(item)

        except Exception as e:
            print('HTML Page Paring Error\n Page: {}'.format(self.driver.current_url))
            print (e)

        #Get next tag, or exit function if self.que == empty
        print('\nFinished Spider Crawl For {}'.format(tag))
        return True









