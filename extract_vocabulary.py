import requests
from bs4 import BeautifulSoup

vocabulary_file = "raw_data/vocabulary.html"
with open(vocabulary_file, 'r', encoding='utf-8') as file:
    html_content = file.read()

soup = BeautifulSoup(html_content, 'html.parser')


def parse_tree(node):
    vocab = []

    # Find all <li> tags at the current level

    for li in node.find_all('li', recursive=True):

        # Extract information from the <a> tag inside the <li>

        a_tag = li.find('a', class_='jstree-anchor')

        if a_tag:

            term = a_tag.get_text(strip=True)

            uri = a_tag.get('data-uri')

            level = li.get('aria-level')

            term_data = {

                'term': term,

                'uri': uri,

                'level': int(level) if level else None,

                'subcategories': []

            }

            # Check if there are child categories (i.e., a <ul> within this <li>)

            ul_tag = li.find('ul', class_='jstree-children')

            if ul_tag:
                term_data['subcategories'] = parse_tree(ul_tag)

            vocab.append(term_data)

    return vocab


# Start parsing from the root <ul> element

root = soup.find('ul', class_='jstree-children')

vocabulary_hierarchy = parse_tree(root)
