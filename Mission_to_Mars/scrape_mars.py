from bs4 import BeautifulSoup as bs
import pymongo
import requests
from splinter import Browser
import os
import pandas as pd
import time
from webdriver_manager.chrome import ChromeDriverManager

# DB Setup
client = pymongo.MongoClient('mongodb://localhost:27017')
db = client.mars_db
collection = db.mars 

def init_browser():
    # @NOTE: Replace the path with your actual path to the chromedriver
    # executable_path = {'executable_path': 'chromedriver.exe'}
    executable_path = {'executable_path': ChromeDriverManager().install()}
    return Browser('chrome', **executable_path, headless=False)

def scrape():
    browser = init_browser()
    collection.drop()

# Mars News
    news_url = 'https://redplanetscience.com/'
    browser.visit(news_url)
    news_html = browser.html
    news_soup = bs(news_html,'lxml')
    try:
        news_title = news_soup.find("div",class_="content_title").text
        news_para = news_soup.find("div", class_="article_teaser_body").text
    except AttributeError:
        return None, None
# JPL Mars Space Images
    jurl = 'https://www.spaceimages-mars.com/'
    browser.visit(jurl)
    button = browser.find_by_tag('button')[1]
    button.click()
    jhtml = browser.html
    jpl_soup = bs(jhtml,"html.parser")
    # image_url = jpl_soup.find('div',class_='fancybox-image"').article.footer.a['data-fancybox-href']
    # try:
    ft_img = jpl_soup.find("img", class_="fancybox-image").get("src")
    # except AttributeError:
#     return None
# print(jurl+ft_img)
    # base_link = "https:"+jpl_soup.find('div', class_='jpl_logo').a['href'].rstrip('/')
    feature_url = jurl+ft_img
    # featured_image_title = jpl_soup.find('h1', class_="media_feature_title").text.strip()

# Mars Facts
    murl = 'https://galaxyfacts-mars.com/'
    table = pd.read_html(murl)
    mars_df = table[0]
    mars_df = mars_df.rename(columns={0: "Mars - Earth Comparison", 1: "Mars", 2: "Earth"})
    mars_df = mars_df.drop(0)
    mars_df =  mars_df[['Mars - Earth Comparison', 'Mars']]
    mars_fact_html = mars_df.to_html(header=False, index=False)
    mars_fact_html.replace("\n", "")

# Mars Hemispheres
    mhurl = 'https://www.marshemispheres.com/'
    browser.visit(mhurl)  
    mhtml = browser.html 
    mh_soup = bs(mhtml,"html.parser") 
    results = mh_soup.find_all("div",class_='item')
    hemisphere_image_urls = []
    for result in results:
            product_dict = {}
            titles = result.find('h3').text
            end_link = result.find("a")["href"]
            image_link = "https://www.marshemispheres.com/" + end_link    
            browser.visit(image_link)
            html = browser.html
            soup= bs(html, "html.parser")
            downloads = soup.find("div", class_="downloads")
            image_url = downloads.find("a")["href"]
            product_dict['title']= titles
            product_dict['image_url']= mhurl+image_url
            hemisphere_image_urls.append(product_dict)

# Close the browser after scraping
    browser.quit()

    # Return results
    mars_data ={
		'news_title' : news_title,
		'summary': news_para,
        'featured_image': feature_url,
		# 'featured_image_title': featured_image_title,
		'fact_table': mars_fact_html,
		'hemisphere_image_urls': hemisphere_image_urls,
        'news_url': news_url,
        'jpl_url': jurl,
        'fact_url': murl,
        'hemisphere_url': mhurl,
        }
    collection.update_one({},{"$set":mars_data},upsert=True)
    print(hemisphere_image_urls)