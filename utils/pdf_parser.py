import fitz

def extract_text_from_pdf(file_path):
    text = ""
    links = set()  # To avoid duplicates

    with fitz.open(file_path) as pdf:
        for page in pdf:
            # Extract text
            text += page.get_text()

            # Extract links (URI type)
            for link in page.get_links():
                if "uri" in link:
                    links.add(link["uri"])

    # Prepend the links at the top
    if links:
        links_text = "links:\n" + "\n".join(links) + "\n\n"
        text = links_text + text

    return text

