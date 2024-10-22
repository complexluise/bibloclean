import json
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Term:
    """Represents a term in the vocabulary hierarchy"""
    notation: str
    label: str
    uri: str
    level: int
    children: list['Term']
    parent_notation: Optional[str] = None


def extract_vocabulary(html_content: str) -> list[Term]:
    """
    Extract vocabulary hierarchy from HTML content

    Args:
        html_content: HTML string containing the vocabulary structure

    Returns:
        Term: Root term with complete hierarchy
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    def extract_term(li_element, parent_notation=None) -> Term:
        # Extract anchor element containing term information
        anchor = li_element.find('a', class_='jstree-anchor')

        # Extract term details
        notation = anchor.find('span', class_='tree-notation').text.strip()

        # Get label by removing the notation from the anchor text
        full_text = anchor.get_text(strip=True)
        label = full_text[full_text.find(notation) + len(notation):].strip()

        # Get URI and level
        uri = anchor.get('data-uri', '')
        level = int(anchor.get('aria-level', 1))

        # Create term object
        term = Term(
            notation=notation,
            label=label,
            uri=uri,
            level=level,
            children=[],
            parent_notation=parent_notation
        )

        # Process children if they exist
        children_ul = li_element.find('ul', class_='jstree-children')
        if children_ul:
            for child_li in children_ul.find_all('li', recursive=False):
                child_term = extract_term(child_li, parent_notation=term.notation)
                term.children.append(child_term)

        return term
    # Find the root element and process the hierarchy
    root_li = soup.find_all('li', role='presentation', attrs={'aria-level': '1'})
    if not root_li:
        raise ValueError("Root element not found in HTML")

    return [extract_term(root_li) for root_li in root_li]


def print_hierarchy(term: Term, indent: int = 0):
    """
    Print the vocabulary hierarchy in a readable format

    Args:
        term: Term object to print
        indent: Current indentation level
    """
    print('  ' * indent + f"{term.notation} - {term.label}")
    for child in term.children:
        print_hierarchy(child, indent + 1)


def save_vocabulary_to_json(vocabulary: list[Term], filename: str):
    """
    Save the vocabulary hierarchy to a JSON file

    Args:
        vocabulary: List of root Term objects
        filename: Name of the JSON file to save
    """
    def term_to_dict(term: Term):
        term_dict = asdict(term)
        term_dict['children'] = [term_to_dict(child) for child in term.children]
        return term_dict

    vocabulary_dict = [term_to_dict(term) for term in vocabulary]

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(vocabulary_dict, f, ensure_ascii=False, indent=2)


# Example usage
if __name__ == "__main__":
    with open('raw_data/vocabulary.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    vocabulary = extract_vocabulary(html_content)

    # Save vocabulary to JSON file
    save_vocabulary_to_json(vocabulary, 'vocabulary.json')

    print("Vocabulary has been saved to vocabulary.json")

    # Optionally, you can still print the hierarchy
    for term in vocabulary:
        print_hierarchy(term)
