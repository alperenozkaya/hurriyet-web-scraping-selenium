import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from msedge.selenium_tools import Edge, EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


driver_path = "F:\\msedgedriver.exe"

edge_options = EdgeOptions()
edge_options.use_chromium = True

driver = Edge(executable_path=driver_path, options=edge_options)

keywords = ['politika', 'siyaset', 'akp', 'mhp', 'erdoğan', 'akşener', 'kılıçdaroğlu']


def translate_turkish_characters(text):
    turkish_to_english = str.maketrans({
        'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
        'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
    })
    return text.translate(turkish_to_english)


def get_article_links(base_url, keyword):
    article_links = []
    driver.maximize_window()
    driver.get(base_url)

    for i in range(1, 101):
        print(f'Keyword: {keyword}, Page: {i}')
        time.sleep(0.01)

        try:
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'news__load-more-button')))
            next_button.click()
        except Exception as e:
            print(f'Exception {e} occurred while trying to click next button.')
            break

    try:
        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        article_containers = soup.find_all('div', class_='tag__list__item')
        links = [div.find('a')['href'] for div in article_containers if div.find('a')]

        print(f'Links: {links}')
        # Ensure full URLs are captured
        full_links = ['https://www.hurriyet.com.tr' + link if link.startswith('/') else link for link in links]
        article_links.extend(full_links)
    except Exception as e:
        print(f'Exception {e} occurred while trying to get links.')

    return article_links


def scrape_article(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f'Error fetching article {url}: {e}')
        return {'title': '', 'content': '', 'alignment': 'center', 'url': url, 'source': 'Hurriyet'}

    article_soup = BeautifulSoup(response.text, 'html.parser')

    title_tag = article_soup.find('h1', class_=['news-detail-title', 'title-actived'])
    title = title_tag.get_text(strip=True) if title_tag else ''

    content_tag = article_soup.find('div', class_=['news-content', 'readingTime'])
    if content_tag:
        paragraphs = content_tag.find_all('p')
        content = ' '.join(p.get_text(strip=True) for p in paragraphs)
    else:
        content = ''

    return {'title': title, 'content': content, 'alignment': 'center', 'url': url, 'source': 'Hurriyet'}


def main():
    all_articles = []

    for keyword in keywords:
        translated_keyword = translate_turkish_characters(keyword)
        main_url = f'https://www.hurriyet.com.tr/haberleri/{translated_keyword}'
        links = get_article_links(main_url, keyword)

        print(f'Number of links for {keyword}: {len(links)}')

        for count, link in enumerate(links):
            print(f'Appending {count + 1}. article for {keyword}')
            article = scrape_article(link)
            if article['title'] and len(article['content']) >= 1000: # skip if title is empty or content is less than 1000 chars
                all_articles.append(article)

    df = pd.DataFrame(all_articles)
    today_date = pd.Timestamp.today().strftime('%Y-%m-%d')
    df.to_excel(f'articles_hurriyet-{today_date}.xlsx', index=False)


if __name__ == "__main__":
    try:
        main()
    finally:
        # Close the Selenium WebDriver
        driver.quit()
