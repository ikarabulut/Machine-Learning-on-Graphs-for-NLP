import requests
import os
import sys
import json
from typing import List
from bs4 import BeautifulSoup

from models.article import Article

mode = sys.argv[1]
I = 0
ROOT_URL = "https://www.ncbi.nlm.nih.gov"
URL = "https://www.ncbi.nlm.nih.gov/pmc/journals/1859/"
page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")
user_agent = "scrapping_script/1.0"
headers = {'User-Agent': user_agent}

if mode == "abstract":
    article_models: List[Article] = []
    job_elements = soup.find_all("a", class_="arc-issue", href=True)
    publication_urls = []
    # loop through each publication
    for job_element in job_elements:
        publication_urls.append(ROOT_URL + job_element["href"])
    # loop through each publication article
    for publication_url in publication_urls:
        article_model = Article
        publications_page = requests.get(publication_url)
        p_soup = BeautifulSoup(publications_page.content, "html.parser")
        publicationlink_divs = p_soup.find_all(
            "div", class_="title")
        for link in publicationlink_divs:
            publication_link = link.find("a", class_="view",  href=True)
            href = publication_link["href"]
            article = requests.get(ROOT_URL + href, headers=headers)
            article_soup = BeautifulSoup(
                article.content, "html.parser")
            abstract = article_soup.find("div", id="abs0010")
            abstract_text = abstract.find_all("p", class_="p p-first-last")
            abstract_text_sb = ""
            for text in abstract_text:
                abstract_text_sb += text.text
            article_model.abstract = abstract_text_sb

            cite_button = article_soup.find("button", class_="citation-button")
            citation_response = requests.get(
                ROOT_URL + cite_button["data-all-citations-url"], headers=headers)
            cite_json = json.loads(citation_response.content)
            article_model.pmid = cite_json["id"]
            article_model.cite = cite_json["nlm"]["format"]

            print(f"ID:: {article_model.pmid} created")
            article_models.append(article_model)
    for article in article_models:
        print(article.pmid)
else:
    job_elements = soup.find_all("a", class_="arc-issue", href=True)
    publication_urls = []
    for job_element in job_elements:
        publication_urls.append(ROOT_URL + job_element["href"])

    for publication_url in publication_urls:
        publications_page = requests.get(publication_url)
        p_soup = BeautifulSoup(publications_page.content, "html.parser")
        rpt_divs = p_soup.find_all(
            "div", class_="rprt")
        for link_div in rpt_divs:
            links_div = link_div.find_all(
                "div", class_="links")
            for link in links_div:
                links = link.find_all(
                    "a", class_="view", href=True, string=lambda text: "pdf" in text.lower())
                for link in links:
                    href = link["href"]
                    user_agent = "scrapping_script/1.0"
                    headers = {'User-Agent': user_agent}
                    pdf = response = requests.get(
                        ROOT_URL + href, headers=headers, stream=True)
                    current_directory = os.getcwd()
                    final_directory = os.path.join(
                        current_directory, f'{href.lstrip("/").replace("/main.pdf", "")}')
                    os.makedirs(final_directory)
                    with open(final_directory + "/main.pdf", 'wb') as f:
                        f.write(response.content)
                        print(f"Files downloaded: {I}")
                        I += 1
