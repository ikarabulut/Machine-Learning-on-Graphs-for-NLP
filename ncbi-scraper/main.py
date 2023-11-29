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

soup = BeautifulSoup(page.content, "html.parser")
user_agent = "scrapping_script/1.5"
headers = {'User-Agent': user_agent}

article_models = ArticleList
article_models.articles = []

job_elements = soup.find_all("a", class_="arc-issue", href=True)
publication_urls = []
# loop through each publication
for job_element in job_elements:
    publication_urls.append(ROOT_URL + job_element["href"])
    # loop through each publication article
for publication_url in publication_urls:
    publications_page = requests.get(publication_url)
    p_soup = BeautifulSoup(publications_page.content, "html.parser")
    publicationlink_divs = p_soup.find_all(
        "div", class_="title")
    for link in publicationlink_divs:
        publication_link = link.find("a", class_="view",  href=True)
        href = publication_link["href"]
        print(ROOT_URL + href)
        article = requests.get(ROOT_URL + href, headers=headers)
        article_soup = BeautifulSoup(
            article.content, "html.parser")

        try:
            # abstract = article_soup.find("div", id="abs0010")
            abstract = article_soup.find("div",
                                         {"id": lambda L: L and L.startswith('abs')})
            abstract_text = abstract.find_all("p", class_="p p-first-last")
        except AttributeError:
            print(f"No Abstract for article {ROOT_URL + href}")
            continue
        abstract_text_sb = ""
        for text in abstract_text:
            abstract_text_sb += text.text
        cite_button = article_soup.find("button", class_="citation-button")
        citation_response = requests.get(
            ROOT_URL + cite_button["data-all-citations-url"], headers=headers)
        cite_json = json.loads(citation_response.content)
        print(cite_json["id"])

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
        location = href + "pdf/main.pdf"
        article_model = Article(
            location="s3://ncbi-safetyandhealth-pdfs" + location, pmid=cite_json["id"], cite=cite_json["nlm"]["format"], abstract=abstract_text_sb)
        print(f"ID:: {article_model.pmid} created")
        article_models.articles.append(article_model)

with open(os.getcwd() + "/publications_dump.json", "w") as f:
    f.write(article_models.model_dump_json())
