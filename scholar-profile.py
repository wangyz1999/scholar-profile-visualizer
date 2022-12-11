import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from tqdm import tqdm
import json


base_url = 'https://scholar.google.com'

# Use headless mode, so you don't have to see the browser
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome('./chromedriver', options=chrome_options)

def get_profile_html(name, sort_by_time=False, more=False):
    """
    Given the name of the scholar, do a name search on Google Scholar
    Return the profile page html of the first scholar (most cited)
    By default, publications are sorted by citations, but you can change sort_by_time=True to sort by time
    Do a click in the "show more" button to show more than 20 works up to 100
    """
    search_url = f"{base_url}/scholar?q={name.replace(' ', '+')}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    profiles = soup.find_all('td', attrs={'valign': 'top'})
    profile_href = profiles[0].find('a')['href']
    profile_url = base_url + profile_href
    if sort_by_time:
        profile_url += "&sortby=pubdate"
    driver.get(profile_url)
    # print(driver.page_source)
    # time.sleep(10)
    if more:
        driver.find_element('id', 'gsc_bpf_more').click()
        time.sleep(0.3)
    profile_html = driver.page_source
    return profile_html
    

def get_work_descriptions(profile_html):
    """
    Given the parsed profile html
    Return a list of work descriptions (up to 100 works)
    """
    work_descs = []
    profile_soup = BeautifulSoup(profile_html, 'html.parser')
    pubs = profile_soup.find_all("tr", attrs={'class': 'gsc_a_tr'})
    for p in tqdm(pubs):
        work_href = p.find('a')['href']
        work_url = base_url + work_href
        work_response = requests.get(work_url)
        time.sleep(0.5)
        work_soup = BeautifulSoup(work_response.text, 'html.parser')
        try:
            desc = work_soup.find(attrs={'id': 'gsc_oci_descr'}).text
            work_descs.append(desc)
        except:
            pass
    return work_descs

def get_interests(profile_html):
    """
    Get the scholar's research direction
    """
    profile_soup = BeautifulSoup(profile_html, 'html.parser')
    pubs = profile_soup.find_all("a", attrs={'class': 'gsc_prf_inta gs_ibl'})
    return [p.text for p in pubs]

def get_index(profile_html):
    """
    Get the scholar's citations and h-index
    """
    profile_soup = BeautifulSoup(profile_html, 'html.parser')
    index = profile_soup.find_all("td", attrs={'class': 'gsc_rsb_std'})
    indexs = [i.text for i in index]
    return indexs[0], indexs[2]


def plot_wordcloud(text, name):
    fig = plt.figure(figsize=(10, 10))
    wordcloud = WordCloud(stopwords=STOPWORDS).generate(text)
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.savefig(f"{name.lower().replace(' ', '_')}.png")

def parse_profile(name):
    profile_html = get_profile_html(name, more=False)
    interests = get_interests(profile_html)
    citations, hindex = get_index(profile_html)
    # work_descriptions = get_work_descriptions(profile_html)
    # all_texts = ' '.join(work_descriptions)
    # plot_wordcloud(all_texts, name)
    desc = {
        "citations": citations,
        "h-index": hindex,
        "interests": interests
    }
    return desc

if __name__ == "__main__":
    # name = 'Geoffrey Hinton'
    # parse_profile(name)

    school = 'harvard'

    descs = dict()
    names = open(f'{school}.txt').read().strip().split('\n')
    for name in tqdm(names):
        try:
            cap_name = name.capitalize()
            desc = parse_profile(cap_name)
            descs[cap_name] = desc
        except:
            pass
    with open(f"{school}.json", "w") as outfile:
        json.dump(descs, outfile, indent=4)
