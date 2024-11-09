from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import time
import traceback
import pandas as pd

# Funkcja do akceptacji plików cookies na avans.pl
def accept_cookies(driver):
    try:
        print("Próba akceptacji cookies...")
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//button[text()="OK, ZGADZAM SIĘ"]')
            )
        )
        accept_button.click()
        print("Cookies zostały zaakceptowane")
    except Exception as e:
        print(f"Błąd podczas akceptacji cookies: {str(e)}")
        with open("cookies_page_source.html", "w") as f:
            f.write(driver.page_source)
        traceback.print_exc()

# Funkcja do klikania w pierwszy produkt na liście wyników
def click_first_product(driver, timeout=30):
    try:
        print("Próba kliknięcia w pierwszy produkt na liście...")
        first_product = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a.a-typo.is-secondary[data-analytics-on="click"]')
            )
        )
        first_product.click()
        print("Kliknięto w pierwszy produkt na liście")
    except (TimeoutException, NoSuchElementException):
        print("Nie udało się kliknąć w pierwszy produkt na liście.")

# Funkcja do pobierania ceny z podziałem na złotówki i grosze
def get_price(driver):
    try:
        print("Próba pobrania ceny ze strony produktu...")
        # Pobranie złotówek
        try:
            price_whole = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span.a-price_price'))
            ).text.strip()
            print(f"Znaleziono część ceny (złotówki): {price_whole}")
        except (TimeoutException, NoSuchElementException):
            print("Nie znaleziono części ceny (złotówki)")
            price_whole = ""

        # Pobranie groszy
        try:
            price_fraction_element = driver.find_element(By.CSS_SELECTOR, 'span.a-price_rest span:not(.a-price_divider)')
            price_fraction = price_fraction_element.text.strip()
            print(f"Znaleziono część ceny (grosze): {price_fraction}")
        except NoSuchElementException:
            print("Nie znaleziono części ceny (grosze)")
            price_fraction = "00"

        # Składamy pełną cenę
        if price_whole:
            price = f"{price_whole}.{price_fraction} zł".strip(". ")
            print(f"Znaleziono pełną cenę: {price}")
        else:
            price = "Nie znaleziono"
            print("Cena nie została znaleziona.")

        return price

    except Exception as e:
        print(f"Błąd podczas pobierania ceny: {str(e)}")
        traceback.print_exc()
        return "Nie znaleziono"

# Funkcja do pobierania ceny bezpośrednio z wyników wyszukiwania
def get_price_from_search_results(driver):
    try:
        print("Próba pobrania ceny z wyników wyszukiwania...")
        # Pobranie złotówek z wyników wyszukiwania
        price_whole = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span.a-price_price'))
        ).text.strip()
        print(f"Znaleziono część ceny (złotówki) w wynikach: {price_whole}")

        # Pobranie groszy z wyników wyszukiwania
        try:
            price_fraction_element = driver.find_element(By.CSS_SELECTOR, 'span.a-price_rest span:not(.a-price_divider)')
            price_fraction = price_fraction_element.text.strip()
            print(f"Znaleziono część ceny (grosze) w wynikach: {price_fraction}")
        except NoSuchElementException:
            print("Nie znaleziono części ceny (grosze) w wynikach")
            price_fraction = "00"

        # Składamy pełną cenę
        price = f"{price_whole}.{price_fraction} zł"
        print(f"Znaleziono cenę w wynikach wyszukiwania: {price}")
        return price

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Błąd podczas pobierania ceny z wyników wyszukiwania: {str(e)}")
        return "Nie znaleziono"

# Funkcja do szukania produktów na avans.pl
def search_avans(driver, product_code):
    base_url = 'https://www.avans.pl/search?query[menu_item]=&query[querystring]='
    search_url = f"{base_url}{product_code}"

    try:
        print(f"Otwieranie URL: {search_url}")
        driver.get(search_url)
        time.sleep(2)

        # Sprawdź, czy istnieje bezpośrednie przekierowanie na stronę produktu
        if "/produkt/" in driver.current_url:
            print("Zostaliśmy przekierowani bezpośrednio na stronę produktu.")
            price = get_price(driver)
        else:
            print("Nie zostaliśmy przekierowani, sprawdzamy listę wyników wyszukiwania.")
            # Spróbuj pobrać cenę bezpośrednio z wyników wyszukiwania
            price = get_price_from_search_results(driver)
            if price == "Nie znaleziono":
                # Jeśli nie znaleziono ceny, kliknij w pierwszy produkt na liście
                click_first_product(driver)
                time.sleep(2)
                price = get_price(driver)

        product_url = driver.current_url
        print(f"Aktualny URL produktu: {product_url}")

    except Exception as e:
        print(f"Błąd podczas przetwarzania {product_code}: {str(e)}")
        with open(f"{product_code}_error_page.html", "w") as f:
            f.write(driver.page_source)
        traceback.print_exc()
        price = 'Nie znaleziono'
        product_url = search_url

    return {
        'Sklep': 'Avans.pl',
        'Kod produktu': product_code,
        'Cena': price,
        'URL': product_url
    }

# Funkcja do zapisu wyników do pliku Excel
def save_to_excel(data, filename="products_prices_avans.xlsx"):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Wyniki zostały zapisane do pliku {filename}")

# Główna funkcja
def main():
    chrome_options = Options()
    service = Service('/Users/bartoszmatyja/Downloads/chromedriver-mac-x64/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    product_codes = ['NWD6602-EU0101F', 'LBE-5AC-LR-EU', 'RE305', 'Archer AX17']
    results = []

    driver.get('https://www.avans.pl/')
    accept_cookies(driver)
    time.sleep(2)

    for code in product_codes:
        result = search_avans(driver, code)
        results.append(result)
        print(f"Wynik dla {code}: {result}\n")

    save_to_excel(results)

    driver.quit()

if __name__ == "__main__":
    main()
