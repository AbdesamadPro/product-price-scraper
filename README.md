# Extracteur de données produits (prix, stock, notes) vers Excel

Un client e-commerce ou une agence a besoin de suivre les prix et la disponibilité de centaines de produits sur un site — le faire à la main prend des heures chaque semaine. Ce script automatise l'extraction complète et livre un fichier Excel prêt à l'emploi en quelques minutes.

**Cas d'usage réels** : veille concurrentielle (suivi de prix), audit de catalogue, alimentation d'un dashboard, préparation de données pour une migration e-commerce.

## Ce que fait le script

- Parcourt automatiquement toutes les pages d'un site (pagination gérée)
- Extrait titre, prix, disponibilité, note pour chaque produit
- Exporte vers Excel ou CSV, avec un résumé statistique immédiat (prix moyen, note moyenne)
- **Robuste** : retries automatiques en cas de coupure réseau, un produit mal formé n'interrompt pas le scraping, messages d'erreur clairs plutôt que des crashs bruts
- **Traçable** : logs horodatés à chaque étape, utile pour livrer un rapport d'exécution à un client

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
# Scraper tout le catalogue
python scraper.py

# Scraper une catégorie précise
python scraper.py --category "Travel"

# Limiter le nombre de pages (utile pour tester rapidement)
python scraper.py --category "Mystery" --max-pages 2

# Exporter en CSV plutôt qu'Excel
python scraper.py --output resultats.csv
```

## Démo

Testé sur [books.toscrape.com](https://books.toscrape.com) (site public dédié à l'entraînement au scraping) : extraction de **1000 produits sur 50 pages** en une seule commande, export Excel avec statistiques automatiques.

## Adapter à un site client

Ce script est une base générique. Pour l'adapter à un autre site e-commerce :

1. Changer `BASE_URL`
2. Inspecter le HTML de la page cible (clic droit → Inspecter) et ajuster les sélecteurs CSS dans `parse_book()` et `get_next_page_url()`
3. Vérifier les CGU et le fichier `/robots.txt` du site cible avant de scraper (voir Aspects juridiques ci-dessous)

## Aspects juridiques

Avant d'utiliser ce script sur un site autre que books.toscrape.com :

- Vérifier que le site n'interdit pas explicitement le scraping dans ses CGU
- Respecter le fichier `robots.txt`
- Ne pas contourner de protections techniques (login, captcha)
- Ne pas collecter de données personnelles (conformité RGPD)
- Privilégier une API officielle quand elle existe

## Stack technique

Python · requests · BeautifulSoup4 · pandas · openpyxl

