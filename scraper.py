"""
Book Scraper - extrait titres, prix, disponibilité et notes
depuis books.toscrape.com (site public conçu pour l'entraînement au scraping).

Usage:
    python scraper.py
    python scraper.py --category "Travel" --max-pages 3
    python scraper.py --output resultats.xlsx

Structuré pour être facilement adapté à un autre site e-commerce :
il suffit de modifier les sélecteurs dans parse_book() et get_next_page_url().
"""

import argparse
import logging
import re
import time
import sys
from dataclasses import dataclass, asdict

import requests
from bs4 import BeautifulSoup
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://books.toscrape.com/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PortfolioScraper/1.0)"}
REQUEST_DELAY = 1.0  # secondes entre chaque requête, pour ne pas surcharger le serveur
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # secondes, multiplié à chaque nouvelle tentative

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


@dataclass
class Book:
    title: str
    price: float
    availability: str
    rating: int
    category: str
    url: str


def get_soup(url: str) -> BeautifulSoup:
    """Récupère et parse une page, avec retries automatiques en cas d'erreur réseau."""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            response.encoding = "utf-8"
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            last_error = e
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF * attempt
                logger.warning(f"Tentative {attempt}/{MAX_RETRIES} échouée pour {url} ({e}). Nouvel essai dans {wait:.0f}s...")
                time.sleep(wait)
            else:
                logger.error(f"Échec définitif après {MAX_RETRIES} tentatives pour {url}: {e}")
    raise last_error


def parse_book(article, category: str) -> Book:
    """Extrait les données d'un livre depuis son bloc HTML."""
    title = article.h3.a["title"]
    price_text = article.select_one(".price_color").text
    match = re.search(r"[\d]+\.?\d*", price_text)
    price = float(match.group()) if match else 0.0
    availability = article.select_one(".availability").text.strip()
    rating_class = article.select_one("p.star-rating")["class"]
    rating = RATING_MAP.get(rating_class[1], 0) if len(rating_class) > 1 else 0
    relative_url = article.h3.a["href"]
    url = BASE_URL + "catalogue/" + relative_url.replace("../../../", "")

    return Book(
        title=title,
        price=price,
        availability=availability,
        rating=rating,
        category=category,
        url=url,
    )


def get_next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    """Retourne l'URL de la page suivante, ou None si dernière page."""
    next_link = soup.select_one("li.next a")
    if not next_link:
        return None
    base = current_url.rsplit("/", 1)[0] + "/"
    return base + next_link["href"]


def scrape_category(category_url: str, category_name: str, max_pages: int | None) -> list[Book]:
    """Scrape toutes les pages d'une catégorie (ou jusqu'à max_pages)."""
    books = []
    url = category_url
    page_count = 0
    skipped = 0

    while url:
        page_count += 1
        logger.info(f"Page {page_count}: {url}")
        soup = get_soup(url)
        articles = soup.select("article.product_pod")

        for article in articles:
            try:
                books.append(parse_book(article, category_name))
            except (AttributeError, TypeError, KeyError) as e:
                skipped += 1
                logger.warning(f"Livre ignoré (HTML inattendu): {e}")

        if max_pages and page_count >= max_pages:
            break

        url = get_next_page_url(soup, url)
        if url:
            time.sleep(REQUEST_DELAY)

    if skipped:
        logger.warning(f"{skipped} livre(s) ignoré(s) au total à cause d'un HTML inattendu.")

    return books


def get_category_url(category_name: str | None) -> tuple[str, str]:
    """Trouve l'URL d'une catégorie par son nom, ou retourne la page d'accueil (toutes catégories)."""
    if not category_name:
        return BASE_URL, "Toutes catégories"

    soup = get_soup(BASE_URL)
    for link in soup.select(".side_categories ul li ul li a"):
        if link.text.strip().lower() == category_name.lower():
            return BASE_URL + link["href"], link.text.strip()

    logger.info(f"Catégorie '{category_name}' introuvable, scraping de toutes les catégories.")
    return BASE_URL, "Toutes catégories"


def export(books: list[Book], output_path: str):
    """Exporte les résultats vers Excel ou CSV selon l'extension."""
    if not books:
        logger.warning("Aucun livre trouvé, rien à exporter.")
        return

    df = pd.DataFrame([asdict(b) for b in books])

    if output_path.endswith(".csv"):
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
    else:
        df.to_excel(output_path, index=False)

    logger.info(f"{len(books)} livres exportés vers {output_path}")
    logger.info(f"Prix moyen: £{df['price'].mean():.2f}")
    logger.info(f"Note moyenne: {df['rating'].mean():.1f}/5")


def main():
    parser = argparse.ArgumentParser(description="Scrape books.toscrape.com")
    parser.add_argument("--category", type=str, default=None,
                         help="Nom de la catégorie à scraper (ex: 'Travel'). Toutes par défaut.")
    parser.add_argument("--max-pages", type=int, default=None,
                         help="Nombre maximum de pages à scraper. Toutes par défaut.")
    parser.add_argument("--output", type=str, default="livres.xlsx",
                         help="Fichier de sortie (.xlsx ou .csv). Par défaut: livres.xlsx")
    args = parser.parse_args()

    try:
        logger.info("Recherche de la catégorie cible...")
        category_url, category_name = get_category_url(args.category)

        logger.info(f"Scraping de la catégorie: {category_name}")
        books = scrape_category(category_url, category_name, args.max_pages)

        export(books, args.output)
    except requests.RequestException:
        logger.error("Le site cible est inaccessible (connexion, timeout, ou blocage). Vérifie ta connexion et réessaie.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrompu par l'utilisateur.")
        sys.exit(0)


if __name__ == "__main__":
    main()
