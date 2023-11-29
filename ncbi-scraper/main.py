import requests
import os
import json
from typing import List
from bs4 import BeautifulSoup

from models.article import Article, ArticleList

I = 0
ROOT_URL = "https://www.ncbi.nlm.nih.gov"
URL = "https://www.ncbi.nlm.nih.gov/pmc/journals/1859/"
page = requests.get(URL)

print(os.getcwd())
soup = BeautifulSoup(page.content, "html.parser")
user_agent = "scrapping_script/1.5"
headers = {'User-Agent': user_agent}

article_models = ArticleList
article_models.articles = []
articles_json_sb = ""
job_elements = soup.find_all("a", class_="arc-issue", href=True)
publication_urls = []

# loop through each publication
for job_element in job_elements:
    publication_urls.append(ROOT_URL + job_element["href"])

    # loop through each url on the page to create a list
for publication_url in publication_urls:
    publications_page = requests.get(publication_url)
    p_soup = BeautifulSoup(publications_page.content, "html.parser")
    publicationlink_divs = p_soup.find_all(
        "div", class_="title")

    # loop through each publication article
    for link in publicationlink_divs:
        publication_link = link.find(
            "a", class_="view",  href=True)
        href = publication_link["href"]
        print(ROOT_URL + href)
        article = requests.get(ROOT_URL + href, headers=headers)
        article_soup = BeautifulSoup(
            article.content, "html.parser")

        pmid_div = article_soup.find("div", class_="fm-citation-pmcid")
        pmcid: str = pmid_div.text.replace("PMCID: ", "")
        cite_button = article_soup.find(
            "button", class_="citation-button")
        nbib_response = requests.get(
            ROOT_URL + cite_button["data-download-format-link"], headers=headers, stream=True)

        if nbib_response.content.decode().__contains__("AB"):
            with open(os.getcwd() + "/nbib" + f"/{pmcid}.nbib", 'wb') as f:
                f.write(nbib_response.content)
            pdf = requests.get(
                ROOT_URL + href + "pdf/main.pdf", headers=headers, stream=True)
            current_directory = os.getcwd()
            final_directory = os.path.join(
                current_directory, f'{href.lstrip("/").replace("/main.pdf", "")}')
            os.makedirs(final_directory)
            with open(final_directory + "/main.pdf", 'wb') as f:
                f.write(pdf.content)

            print(f"Files downloaded: {I}")
            I += 1
