from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import re
import urllib.parse
from utils import save_raw_data

# Your ChromeDriver path
CHROME_DRIVER_PATH = r"E:\chromedriver-win64\chromedriver-win64\chromedriver.exe"

# URL to scrape
URL = "https://brokeragebd.com/"

def normalize_price(price_str):
    """Convert price strings containing Crore/Lakh/Thousand into numeric BDT."""
    if not isinstance(price_str, str):
        return None

    price = price_str.lower().replace(",", "").replace("bdt", "").replace("tk", "").strip()
    if not price:
        return None

    multiplier = 1
    if "crore" in price:
        multiplier = 10_000_000
    elif "lakh" in price or "lac" in price:
        multiplier = 100_000
    elif "thousand" in price or "k" in price:
        multiplier = 1_000

    numbers = re.findall(r"[\d.]+", price)
    if not numbers:
        return None

    value = float(numbers[0]) * multiplier
    return round(value, 2)


def extract_info_from_title(title):
    """Extract area, bedrooms, location, and For (Rent/Sell) from title.
    Example: '1437 sft 3-bedroom flat is ready for sale in Uttara'
    """
    info = {"area_sqft": None, "bedrooms": None, "location": None, "for_rent_sell": None}
    
    if title and title != "N/A":
        title_lower = title.lower()
        # Extract area: "1437 sft" or "1437sft"
        area_match = re.search(r'(\d+)\s*sft', title_lower)
        if area_match:
            info["area_sqft"] = int(area_match.group(1))
        
        # Extract bedrooms: "3-bedroom" or "3 bedroom"
        bedroom_match = re.search(r'(\d+)[-\s]*bedroom', title_lower)
        if bedroom_match:
            info["bedrooms"] = int(bedroom_match.group(1))
        
        # Extract location: text after "in" (e.g., "in Uttara")
        location_match = re.search(r'in\s+([^,]+?)(?:\s|$|,|\.)', title, re.IGNORECASE)
        if location_match:
            info["location"] = location_match.group(1).strip()
        
        # Extract For (Rent/Sell) from title
        if "for rent" in title_lower or "rent" in title_lower:
            info["for_rent_sell"] = "Rent"
        elif "for sale" in title_lower or "sale" in title_lower:
            info["for_rent_sell"] = "Sell"
    
    return info

def extract_info_from_url(url):
    """Extract area, bedrooms, location, and For (Rent/Sell) from URL structure."""
    info = {"area_sqft": None, "bedrooms": None, "location": None, "for_rent_sell": None, "property_type": None}
    
    if url and url != "N/A":
        url_lower = url.lower()
        # Pattern: ...1437-sft-3-bedroom-flat-is-ready-for-sale-in-uttara-k8/
        area_match = re.search(r'(\d+)-sft', url_lower)
        bedroom_match = re.search(r'(\d+)-bedroom', url_lower)
        location_match = re.search(r'in-([^/]+)', url_lower)
        
        if area_match:
            info["area_sqft"] = int(area_match.group(1))
        if bedroom_match:
            info["bedrooms"] = int(bedroom_match.group(1))
        if location_match:
            info["location"] = location_match.group(1).replace('-', ' ').title()
        
        # Extract For (Rent/Sell) from URL
        if "for-rent" in url_lower or "rent" in url_lower:
            info["for_rent_sell"] = "Rent"
        elif "for-sale" in url_lower or "sale" in url_lower:
            info["for_rent_sell"] = "Sell"
        
        # Extract property type from URL
        if "flat" in url_lower:
            info["property_type"] = "Flat"
        elif "apartment" in url_lower:
            info["property_type"] = "Apartment"
        elif "house" in url_lower:
            info["property_type"] = "House"
    
    return info

def scrape_property_detail(driver, url):
    """Scrape detailed information from individual property page."""
    detail = {
        "area_sqft": None,
        "bedrooms": None,
        "bathrooms": None,
        "floor": None,
        "for_rent_sell": None,
        "price": None,
        "location": None,
        "property_type": None
    }
    
    try:
        driver.get(url)
        time.sleep(2)  # Wait for page to load
        
        # Try to find area - look for text containing "sft" or "sqft"
        try:
            # Try multiple approaches
            area_xpaths = [
                "//*[contains(text(), 'sft') or contains(text(), 'sqft') or contains(text(), 'Sq Ft')]",
                "//*[contains(., 'sft') or contains(., 'sqft')]"
            ]
            for xpath in area_xpaths:
                try:
                    area_elems = driver.find_elements(By.XPATH, xpath)
                    for elem in area_elems:
                        area_text = elem.text
                        area_match = re.search(r'(\d+)', area_text.replace(',', ''))
                        if area_match:
                            area_val = int(area_match.group(1))
                            if 100 <= area_val <= 10000:  # Reasonable range for sqft
                                detail["area_sqft"] = area_val
                                break
                    if detail["area_sqft"]:
                        break
                except:
                    continue
        except:
            pass
        
        # Try to find bedrooms
        try:
            bedroom_xpaths = [
                "//*[contains(text(), 'Bedroom') or contains(text(), 'bedroom')]",
                "//*[contains(., 'bedroom')]"
            ]
            for xpath in bedroom_xpaths:
                try:
                    bedroom_elems = driver.find_elements(By.XPATH, xpath)
                    for elem in bedroom_elems:
                        bedroom_text = elem.text
                        bedroom_match = re.search(r'(\d+)[-\s]*bedroom', bedroom_text.lower())
                        if bedroom_match:
                            detail["bedrooms"] = int(bedroom_match.group(1))
                            break
                    if detail["bedrooms"]:
                        break
                except:
                    continue
        except:
            pass
        
        # Try to find price - look for "BDT", "Tk", "Lakh", "Crore"
        price_selectors = [
            'span.item-price',
            '.price',
            '[class*="price"]',
            '//*[contains(text(), "BDT")]',
            '//*[contains(text(), "Tk")]',
            '//*[contains(text(), "Lakh")]',
            '//*[contains(text(), "Crore")]'
        ]
        for selector in price_selectors:
            try:
                if selector.startswith('//'):
                    price_elems = driver.find_elements(By.XPATH, selector)
                else:
                    price_elems = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for price_elem in price_elems:
                    price_text = price_elem.text.strip()
                    if any(keyword in price_text for keyword in ['BDT', 'Tk', 'Lakh', 'Crore', 'lakh', 'crore']):
                        detail["price"] = price_text
                        break
                
                if detail["price"]:
                    break
            except:
                continue
        
        # Try to find bathrooms
        try:
            bathroom_xpaths = [
                "//*[contains(text(), 'Bathroom') or contains(text(), 'bathroom')]",
                "//*[contains(., 'bathroom')]",
                "//*[contains(text(), 'Bath') or contains(text(), 'bath')]"
            ]
            for xpath in bathroom_xpaths:
                try:
                    bathroom_elems = driver.find_elements(By.XPATH, xpath)
                    for elem in bathroom_elems:
                        bathroom_text = elem.text
                        bathroom_match = re.search(r'(\d+)[-\s]*(?:bathroom|bath)', bathroom_text.lower())
                        if bathroom_match:
                            detail["bathrooms"] = int(bathroom_match.group(1))
                            break
                    if detail["bathrooms"]:
                        break
                except:
                    continue
        except:
            pass
        
        # Try to find floor
        try:
            floor_xpaths = [
                "//*[contains(text(), 'Floor') or contains(text(), 'floor')]",
                "//*[contains(., 'floor')]",
                "//*[contains(text(), 'Level') or contains(text(), 'level')]"
            ]
            for xpath in floor_xpaths:
                try:
                    floor_elems = driver.find_elements(By.XPATH, xpath)
                    for elem in floor_elems:
                        floor_text = elem.text
                        # Look for patterns like "3rd Floor", "Floor 5", "5th floor", etc.
                        floor_match = re.search(r'(?:floor|level)[\s:]*(\d+)', floor_text.lower())
                        if not floor_match:
                            floor_match = re.search(r'(\d+)(?:st|nd|rd|th)?[\s]*(?:floor|level)', floor_text.lower())
                        if floor_match:
                            detail["floor"] = int(floor_match.group(1))
                            break
                    if detail["floor"]:
                        break
                except:
                    continue
        except:
            pass
        
        # Try to find For (Rent/Sell) - check URL and page content
        try:
            # Check URL first
            url_lower = url.lower()
            if "rent" in url_lower:
                detail["for_rent_sell"] = "Rent"
            elif "sale" in url_lower or "sell" in url_lower:
                detail["for_rent_sell"] = "Sell"
            
            # Also check page content
            if not detail["for_rent_sell"]:
                page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                if "for rent" in page_text or "available for rent" in page_text:
                    detail["for_rent_sell"] = "Rent"
                elif "for sale" in page_text or "available for sale" in page_text:
                    detail["for_rent_sell"] = "Sell"
            
            # Check price text for rent indicators
            if detail["price"]:
                price_lower = detail["price"].lower()
                if "per month" in price_lower or "monthly" in price_lower or "rent" in price_lower:
                    detail["for_rent_sell"] = "Rent"
                elif "crore" in price_lower or "lakh" in price_lower:
                    if not detail["for_rent_sell"]:
                        detail["for_rent_sell"] = "Sell"
        except:
            pass
        
        # Try to find property type
        try:
            property_type_xpaths = [
                "//*[contains(text(), 'Flat') or contains(text(), 'Apartment') or contains(text(), 'House')]",
                "//*[contains(., 'property type')]"
            ]
            for xpath in property_type_xpaths:
                try:
                    type_elems = driver.find_elements(By.XPATH, xpath)
                    for elem in type_elems:
                        type_text = elem.text.lower()
                        if "flat" in type_text:
                            detail["property_type"] = "Flat"
                            break
                        elif "apartment" in type_text:
                            detail["property_type"] = "Apartment"
                            break
                        elif "house" in type_text:
                            detail["property_type"] = "House"
                            break
                    if detail["property_type"]:
                        break
                except:
                    continue
            
            # Also check URL
            if not detail["property_type"]:
                url_lower = url.lower()
                if "flat" in url_lower:
                    detail["property_type"] = "Flat"
                elif "apartment" in url_lower:
                    detail["property_type"] = "Apartment"
                elif "house" in url_lower:
                    detail["property_type"] = "House"
        except:
            pass
        
        # Try to find location
        location_selectors = [
            'address.item-address',
            '.location',
            '[class*="location"]',
            '[class*="address"]',
            '//address',
            '//*[contains(@class, "location")]',
            '//*[contains(@class, "address")]'
        ]
        for selector in location_selectors:
            try:
                if selector.startswith('//'):
                    location_elems = driver.find_elements(By.XPATH, selector)
                else:
                    location_elems = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for location_elem in location_elems:
                    loc_text = location_elem.text.strip()
                    if loc_text and loc_text != "N/A" and len(loc_text) > 2:
                        detail["location"] = loc_text
                        break
                
                if detail["location"]:
                    break
            except:
                continue
            
    except Exception as e:
        print(f"    Error scraping detail page: {e}")
    
    return detail

def find_and_click_next_button(driver):
    """Find and click the next page button. Returns True if successful, False otherwise."""
    next_selectors = [
        "//a[contains(text(), 'Next')]",
        "//a[contains(text(), 'next')]",
        "//a[contains(@class, 'next')]",
        "//a[contains(@class, 'pagination-next')]",
        "//a[@rel='next']",
        "//li[@class='next']//a",
        "//li[contains(@class, 'next')]//a",
        "//a[contains(@aria-label, 'Next')]",
        "//button[contains(text(), 'Next')]",
        "//span[contains(text(), 'Next')]/parent::a",
        "//a[contains(., '→')]",
        "//a[contains(., '›')]",
        "//a[contains(., '»')]",
        "//*[@class='pagination']//a[last()]",  # Last link in pagination
        "//*[contains(@class, 'pagination')]//a[contains(text(), '>')]",
        "//*[contains(@class, 'pagination')]//a[contains(text(), '›')]"
    ]
    
    # Also try to find by page numbers - look for current page + 1
    try:
        # Find all pagination links
        pagination_links = driver.find_elements(By.CSS_SELECTOR, '.pagination a, [class*="pagination"] a, .page-numbers a')
        for link in pagination_links:
            try:
                link_text = link.text.strip()
                # Check if it's a number greater than current page or contains next indicators
                if link_text.isdigit():
                    continue  # Skip numbered pages for now
                elif any(indicator in link_text.lower() for indicator in ['next', '→', '›', '»', '>']):
                    if link.is_displayed() and link.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView(true);", link)
                        time.sleep(0.5)
                        link.click()
                        time.sleep(3)
                        return True
            except:
                continue
    except:
        pass
    
    # Try the XPath selectors
    for selector in next_selectors:
        try:
            next_buttons = driver.find_elements(By.XPATH, selector)
            for next_button in next_buttons:
                try:
                    if next_button.is_displayed() and next_button.is_enabled():
                        # Check if it's not disabled
                        classes = next_button.get_attribute("class") or ""
                        if "disabled" not in classes.lower():
                            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                            time.sleep(0.5)
                            next_button.click()
                            time.sleep(3)  # Wait for page to load
                            return True
                except:
                    continue
        except:
            continue
    
    return False

# Setup Chrome driver
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])

service = Service(CHROME_DRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

print("="*60)
print("Starting scraping process...")
print("="*60)

# Step 1: Collect all URLs from all pages
print("\n" + "="*60)
print("STEP 1: Collecting all property URLs from all pages...")
print("="*60)

all_urls = []
all_titles = []
all_card_data = {}  # Store basic card data for each URL
page_num = 1
max_pages = 500  # Increased limit to get more listings
previous_page_urls = set()  # Track URLs from previous page to detect duplicates

while page_num <= max_pages:
    print(f"\n--- Page {page_num} ---")
    
    if page_num == 1:
        print("Opening website...")
        driver.get(URL)
    else:
        # Already navigated by clicking next button
        pass
    
    # Wait for the page to load
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.item-listing-wrap')))
        print("Page loaded successfully.")
    except TimeoutException:
        print("Error: Page took too long to load or element not found.")
        break
    
    # Scroll to load all listings on current page (for infinite scroll or lazy loading)
    print("Scrolling to load all listings...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_scrolls = 15  # Increased scroll attempts
    no_change_count = 0
    
    while scroll_attempts < max_scrolls:
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2.5)  # Wait for content to load
        
        # Also try scrolling incrementally
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(1)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            no_change_count += 1
            if no_change_count >= 3:  # If no change 3 times in a row, stop
                break
        else:
            no_change_count = 0
        last_height = new_height
        scroll_attempts += 1
        
        # Check how many listings we have so far
        current_cards = driver.find_elements(By.CSS_SELECTOR, 'div.item-listing-wrap')
        if scroll_attempts % 3 == 0:
            print(f"    Scroll {scroll_attempts}: Found {len(current_cards)} listings so far...")
    
    # Final scroll to top to ensure everything is loaded
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    
    # Try multiple selectors to find all listing cards
    cards = []
    card_selectors = [
        'div.item-listing-wrap',
        '.item-listing-wrap',
        '[class*="item-listing"]',
        '[class*="listing-item"]',
        '.property-item',
        '[class*="property-card"]'
    ]
    
    for selector in card_selectors:
        try:
            found_cards = driver.find_elements(By.CSS_SELECTOR, selector)
            if len(found_cards) > len(cards):
                cards = found_cards
                print(f"Found {len(cards)} listings using selector: {selector}")
        except:
            continue
    
    # Also try to find all property links directly (this catches everything)
    direct_urls_found = 0
    try:
        property_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/property/"]')
        print(f"Also found {len(property_links)} property links directly")
        
        # Collect all unique property URLs
        for link in property_links:
            try:
                url = link.get_attribute("href")
                if url and url not in all_urls and "/property/" in url:
                    # Clean URL (remove fragments, ensure it's complete)
                    if "#" in url:
                        url = url.split("#")[0]
                    if url not in all_urls:
                        all_urls.append(url)
                        direct_urls_found += 1
                        try:
                            title = link.text.strip() or link.get_attribute("title") or "N/A"
                        except:
                            title = "N/A"
                        
                        # Try to get location and price from nearby elements
                        location = None
                        price = None
                        try:
                            # Look for parent or sibling elements
                            parent = link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'item') or contains(@class, 'listing')]")
                            try:
                                loc_elem = parent.find_element(By.CSS_SELECTOR, 'address, [class*="address"], [class*="location"]')
                                location = loc_elem.text.strip()
                            except:
                                pass
                            try:
                                price_elem = parent.find_element(By.CSS_SELECTOR, '[class*="price"]')
                                price = price_elem.text.strip()
                            except:
                                pass
                        except:
                            pass
                        
                        if url not in all_card_data:
                            all_card_data[url] = {
                                "title": title,
                                "location": location,
                                "price": price
                            }
            except:
                continue
        
        if direct_urls_found > 0:
            print(f"Added {direct_urls_found} new URLs from direct link search")
    except Exception as e:
        print(f"Error in direct link search: {e}")
    
    print(f"Total listings found on page {page_num}: {len(cards)}")
    
    if len(cards) == 0 and len(all_urls) == 0:
        print("No listings found. Stopping.")
        break
    
    # Collect URLs and basic info from current page cards
    page_urls_count = 0
    current_page_urls = set()
    
    for card in cards:
        try:
            # Try multiple selectors for the link
            url = None
            url_elem = None
            
            link_selectors = [
                'h2.item-title a',
                'h2 a',
                '.item-title a',
                'a[href*="/property/"]',
                'a'
            ]
            
            for link_selector in link_selectors:
                try:
                    url_elem = card.find_element(By.CSS_SELECTOR, link_selector)
                    url = url_elem.get_attribute("href")
                    if url and "/property/" in url:
                        break
                except:
                    continue
            
            if not url or url in all_urls:
                continue
            
            all_urls.append(url)
            current_page_urls.add(url)
            page_urls_count += 1
            
            # Extract basic info from card
            try:
                title = url_elem.text.strip() if url_elem else "N/A"
            except:
                title = "N/A"
            
            location = None
            location_selectors = [
                'address.item-address',
                'address',
                '.item-address',
                '[class*="address"]',
                '[class*="location"]'
            ]
            for loc_selector in location_selectors:
                try:
                    location = card.find_element(By.CSS_SELECTOR, loc_selector).text.strip()
                    if location:
                        break
                except:
                    continue
            
            price = None
            price_selectors = [
                'span.item-price',
                '.item-price',
                '[class*="price"]'
            ]
            for price_selector in price_selectors:
                try:
                    price = card.find_element(By.CSS_SELECTOR, price_selector).text.strip()
                    if price:
                        break
                except:
                    continue
            
            # Store card data
            all_card_data[url] = {
                "title": title,
                "location": location,
                "price": price
            }
        except Exception as e:
            print(f"    Error extracting from card: {e}")
            continue
    
    print(f"Collected {page_urls_count} new URLs from cards on page {page_num}. Total: {len(all_urls)}")
    
    # Debug: Show what we found
    if page_num == 1 and len(all_urls) <= 20:
        print(f"\n    DEBUG: First page analysis:")
        print(f"      - Cards found: {len(cards)}")
        print(f"      - Direct links found: {direct_urls_found}")
        print(f"      - Total URLs collected: {len(all_urls)}")
        if len(all_urls) > 0:
            print(f"      - Sample URLs:")
            for i, url in enumerate(all_urls[:5], 1):
                print(f"        {i}. {url}")
    
    # Check if we're seeing the same URLs (stuck on same page)
    if current_page_urls == previous_page_urls and page_num > 1:
        print("    ⚠ Warning: Same URLs detected as previous page. May be stuck.")
        # Still try to go to next page
    
    previous_page_urls = current_page_urls.copy()
    
    # Try to go to next page - try multiple methods
    print(f"Looking for next page...")
    current_url_before = driver.current_url
    next_clicked = False
    
    # Method 0: Collect all page numbers and navigate systematically
    all_page_numbers = []
    try:
        page_links = driver.find_elements(By.CSS_SELECTOR, '.pagination a, [class*="pagination"] a, .page-numbers a, .pager a, nav a, [role="navigation"] a')
        for link in page_links:
            try:
                link_text = link.text.strip()
                link_href = link.get_attribute("href") or ""
                
                page_num_from_text = None
                page_num_from_url = None
                
                # Get page number from text
                if link_text.isdigit():
                    page_num_from_text = int(link_text)
                
                # Get page number from URL
                if "page=" in link_href.lower():
                    match = re.search(r'page[=_](\d+)', link_href, re.IGNORECASE)
                    if match:
                        page_num_from_url = int(match.group(1))
                elif "/page/" in link_href.lower():
                    match = re.search(r'/page/(\d+)', link_href, re.IGNORECASE)
                    if match:
                        page_num_from_url = int(match.group(1))
                
                page_num_found = page_num_from_text or page_num_from_url
                if page_num_found and page_num_found not in all_page_numbers:
                    all_page_numbers.append(page_num_found)
            except:
                continue
        
        if all_page_numbers:
            all_page_numbers.sort()
            print(f"    Found page numbers: {all_page_numbers}")
            
            # If we have page numbers, try to go to the next one
            if page_num + 1 in all_page_numbers:
                for link in page_links:
                    try:
                        link_text = link.text.strip()
                        link_href = link.get_attribute("href") or ""
                        
                        # Check if this link goes to page_num + 1
                        is_target_page = False
                        if link_text.isdigit() and int(link_text) == page_num + 1:
                            is_target_page = True
                        elif page_num + 1 in [int(m.group(1)) for m in re.finditer(r'page[=_](\d+)', link_href, re.IGNORECASE)]:
                            is_target_page = True
                        elif page_num + 1 in [int(m.group(1)) for m in re.finditer(r'/page/(\d+)', link_href, re.IGNORECASE)]:
                            is_target_page = True
                        
                        if is_target_page and link.is_displayed() and link.is_enabled():
                            driver.execute_script("arguments[0].scrollIntoView(true);", link)
                            time.sleep(0.5)
                            link.click()
                            time.sleep(3)
                            print(f"    ✓ Clicked page {page_num + 1} from page numbers list")
                            # Set next_clicked and skip other methods
                            next_clicked = True
                            break
                    except:
                        continue
    except Exception as e:
        print(f"    Error collecting page numbers: {e}")
    
    # Method 1: Try next button (only if Method 0 didn't work)
    if not next_clicked:
        next_clicked = find_and_click_next_button(driver)
    
    # Method 2: If next button didn't work, try clicking page numbers
    if not next_clicked:
        try:
            # Try to find and click the next page number
            page_links = driver.find_elements(By.CSS_SELECTOR, '.pagination a, [class*="pagination"] a, .page-numbers a, .pager a, nav a, [role="navigation"] a')
            print(f"    Found {len(page_links)} pagination links")
            
            # Print all pagination links for debugging
            if len(page_links) > 0:
                print(f"    Pagination links found:")
                for i, link in enumerate(page_links[:10]):  # Show first 10
                    try:
                        link_text = link.text.strip()
                        link_href = link.get_attribute("href")
                        print(f"      {i+1}. Text: '{link_text}', Href: {link_href[:80] if link_href else 'None'}")
                    except:
                        pass
            
            for link in page_links:
                try:
                    link_text = link.text.strip()
                    link_href = link.get_attribute("href") or ""
                    
                    # If we're on page N, look for page N+1
                    if link_text.isdigit():
                        link_num = int(link_text)
                        if link_num == page_num + 1:
                            if link.is_displayed() and link.is_enabled():
                                driver.execute_script("arguments[0].scrollIntoView(true);", link)
                                time.sleep(0.5)
                                link.click()
                                next_clicked = True
                                print(f"    ✓ Clicked page number {link_num}")
                                break
                    # Also check href for page numbers
                    elif "page=" in link_href.lower() or "/page/" in link_href.lower():
                        # Extract page number from URL
                        if "page=" in link_href:
                            page_match = re.search(r'page[=_](\d+)', link_href, re.IGNORECASE)
                        elif "/page/" in link_href:
                            page_match = re.search(r'/page/(\d+)', link_href, re.IGNORECASE)
                        else:
                            page_match = None
                        
                        if page_match:
                            link_num = int(page_match.group(1))
                            if link_num == page_num + 1:
                                if link.is_displayed() and link.is_enabled():
                                    driver.execute_script("arguments[0].scrollIntoView(true);", link)
                                    time.sleep(0.5)
                                    link.click()
                                    next_clicked = True
                                    print(f"    ✓ Clicked page {link_num} via href")
                                    break
                except Exception as e:
                    continue
        except Exception as e:
            print(f"    Error in page number method: {e}")
    
    # Method 3: Try URL-based pagination
    if not next_clicked:
        try:
            # Check if URL has page parameter we can modify
            if "page=" in current_url_before:
                parsed = urllib.parse.urlparse(current_url_before)
                params = urllib.parse.parse_qs(parsed.query)
                if 'page' in params:
                    current_page = int(params['page'][0])
                    next_page = current_page + 1
                    # Build next page URL
                    params['page'] = [str(next_page)]
                    new_query = urllib.parse.urlencode(params, doseq=True)
                    next_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
                    driver.get(next_url)
                    next_clicked = True
                    print(f"Navigated to page {next_page} via URL")
            elif page_num == 1:
                # Try multiple URL patterns for page 2
                url_patterns = [
                    current_url_before + ("&" if "?" in current_url_before else "?") + "page=2",
                    current_url_before + ("&" if "?" in current_url_before else "?") + "paged=2",
                    current_url_before + "/page/2",
                    current_url_before + "/2",
                ]
                
                for next_url in url_patterns:
                    try:
                        print(f"    Trying URL pattern: {next_url}")
                        driver.get(next_url)
                        time.sleep(3)
                        # Check if page loaded successfully
                        cards_check = driver.find_elements(By.CSS_SELECTOR, 'div.item-listing-wrap')
                        if len(cards_check) > 0:
                            # Verify we got different listings
                            test_urls = []
                            for card in cards_check[:3]:
                                try:
                                    url_elem = card.find_element(By.CSS_SELECTOR, 'h2.item-title a')
                                    test_url = url_elem.get_attribute("href")
                                    if test_url:
                                        test_urls.append(test_url)
                                except:
                                    pass
                            
                            # If we got URLs and they're different from what we have, it worked
                            if test_urls and any(url not in all_urls for url in test_urls):
                                next_clicked = True
                                print(f"    ✓ Navigated to page 2 via URL: {next_url}")
                                break
                    except Exception as e:
                        continue
        except Exception as e:
            print(f"    URL pagination attempt failed: {e}")
    
    if next_clicked:
        time.sleep(3)  # Wait for page transition
        current_url_after = driver.current_url
        
        # Check if URL actually changed or if we got new listings
        if current_url_before != current_url_after:
            page_num += 1
            print(f"Successfully navigated to page {page_num}")
        else:
            # Check if we're getting new listings
            time.sleep(2)
            new_cards = driver.find_elements(By.CSS_SELECTOR, 'div.item-listing-wrap')
            if len(new_cards) > 0:
                # Check if these are new URLs
                new_urls_found = False
                for card in new_cards[:3]:  # Check first 3
                    try:
                        url_elem = card.find_element(By.CSS_SELECTOR, 'h2.item-title a')
                        url = url_elem.get_attribute("href")
                        if url and url not in all_urls:
                            new_urls_found = True
                            break
                    except:
                        continue
                
                if new_urls_found:
                    page_num += 1
                    print(f"Found new listings, continuing to page {page_num}")
                else:
                    print("No new listings found. May have reached last page.")
                    break
            else:
                print("Next button clicked but no new listings. May have reached last page.")
                break
    else:
        # Last resort: Try manually constructing page URLs
        if page_num == 1 and len(all_urls) < 200:
            print("    ⚠ Only found a few listings. Trying manual page navigation...")
            manual_pages_tried = 0
            max_manual_pages = 100  # Try up to 100 pages to get more listings
            manual_page_found = False
            
            for manual_page in range(2, max_manual_pages + 1):
                try:
                    # Try different URL patterns
                    base_url = current_url_before.rstrip('/')
                    test_urls = [
                        f"{base_url}?page={manual_page}",
                        f"{base_url}?paged={manual_page}",
                        f"{base_url}/page/{manual_page}",
                        f"{base_url}/{manual_page}",
                    ]
                    
                    found_new_page = False
                    for test_url in test_urls:
                        try:
                            print(f"    Trying manual page {manual_page}: {test_url}")
                            driver.get(test_url)
                            time.sleep(3)
                            
                            # Check if we got listings
                            test_cards = driver.find_elements(By.CSS_SELECTOR, 'div.item-listing-wrap')
                            if len(test_cards) > 0:
                                # Check if these are new URLs
                                new_urls_count = 0
                                for card in test_cards[:5]:
                                    try:
                                        url_elem = card.find_element(By.CSS_SELECTOR, 'h2.item-title a')
                                        test_url_val = url_elem.get_attribute("href")
                                        if test_url_val and test_url_val not in all_urls:
                                            new_urls_count += 1
                                    except:
                                        continue
                                
                                if new_urls_count > 0:
                                    found_new_page = True
                                    page_num = manual_page
                                    manual_page_found = True
                                    print(f"    ✓ Found page {manual_page} with new listings! Continuing main loop...")
                                    manual_pages_tried = 0  # Reset counter
                                    break
                        except:
                            continue
                    
                    if not found_new_page:
                        manual_pages_tried += 1
                        if manual_pages_tried >= 3:  # If 3 consecutive pages fail, stop
                            print(f"    No more pages found after trying {manual_page - 1} pages")
                            break
                    else:
                        # Found a new page, continue the main loop
                        break
                except Exception as e:
                    print(f"    Error trying manual page {manual_page}: {e}")
                    continue
            
            if not manual_page_found:
                print("No next page found. Finished collecting URLs.")
                break
            # If manual_page_found is True, we continue the main while loop
        else:
            print("No next page found. Finished collecting URLs.")
            break

print(f"\n{'='*60}")
print(f"STEP 1 Complete: Collected {len(all_urls)} total property URLs")
print(f"{'='*60}")
print(f"\nSummary:")
print(f"  - Total unique URLs collected: {len(all_urls)}")
print(f"  - Total pages processed: {page_num}")
print(f"  - Card data stored: {len(all_card_data)}")
if len(all_urls) > 0:
    print(f"\nSample URLs (first 3):")
    for i, url in enumerate(all_urls[:3], 1):
        print(f"  {i}. {url}")

# Step 2: Visit each URL to get detailed information
print(f"\n{'='*60}")
print(f"STEP 2: Visiting each property page to collect detailed information...")
print(f"{'='*60}")

data = []

for idx, url in enumerate(all_urls, 1):
    print(f"\n[{idx}/{len(all_urls)}] Processing: {url[:80]}...")
    
    try:
        # Get basic info from card data
        card_info = all_card_data.get(url, {})
        title = card_info.get("title", "N/A")
        card_location = card_info.get("location")
        card_price = card_info.get("price")
        
        # Extract info from title
        title_info = extract_info_from_title(title)
        
        # Extract info from URL
        url_info = extract_info_from_url(url)
        
        # Visit detail page to get complete information
        detail = scrape_property_detail(driver, url)
        
        # Combine all sources: detail page > title > URL > card
        area_sqft = detail["area_sqft"] or title_info["area_sqft"] or url_info["area_sqft"]
        bedrooms = detail["bedrooms"] or title_info["bedrooms"] or url_info["bedrooms"]
        price = detail["price"] or card_price
        price_numeric = normalize_price(price) if price else None
        location = detail["location"] or card_location or title_info["location"] or url_info["location"]
        floor = detail["floor"]
        for_rent_sell = detail["for_rent_sell"] or title_info["for_rent_sell"] or url_info["for_rent_sell"]
        bathrooms = detail["bathrooms"]
        property_type = detail["property_type"] or url_info["property_type"]
        
        # Build the data record with all columns
        record = {
            "Location": location if location else "N/A",
            "Area_sqft": area_sqft if area_sqft else "N/A",
            "Price": price if price else "N/A",
            "Price_BDT": price_numeric if price_numeric else "N/A",
            "Bedroom": bedrooms if bedrooms else "N/A",
            "Bathroom": bathrooms if bathrooms else "N/A",
            "Floor": floor if floor else "N/A",
            "For": for_rent_sell if for_rent_sell else "N/A",
            "Property_Type": property_type if property_type else "N/A",
            "URL": url
        }
        
        data.append(record)
        print(f"  ✓ Collected: Location={location[:25] if location else 'N/A'}, Area={area_sqft}, Bed={bedrooms}, Bath={bathrooms}, Floor={floor}, For={for_rent_sell}, Price={price[:25] if price else 'N/A'}")
        
    except Exception as e:
        print(f"  ✗ Error processing URL: {e}")
        # Still add a record with available data to ensure we don't lose rows
        card_info = all_card_data.get(url, {})
        title_info = extract_info_from_title(card_info.get("title", ""))
        url_info = extract_info_from_url(url)
        
        # Normalize price if available
        price_text = card_info.get("price") or "N/A"
        price_bdt = normalize_price(price_text) if price_text != "N/A" else None
        
        record = {
            "Location": card_info.get("location") or title_info["location"] or url_info["location"] or "N/A",
            "Area_sqft": title_info["area_sqft"] or url_info["area_sqft"] or "N/A",
            "Price": price_text,
            "Price_BDT": price_bdt if price_bdt else "N/A",
            "Bedroom": title_info["bedrooms"] or url_info["bedrooms"] or "N/A",
            "Bathroom": "N/A",
            "Floor": "N/A",
            "For": title_info["for_rent_sell"] or url_info["for_rent_sell"] or "N/A",
            "Property_Type": url_info["property_type"] or "N/A",
            "URL": url
        }
        data.append(record)
        continue

driver.quit()

# Check if data is collected correctly
if not data:
    print("\n" + "="*60)
    print("No data was collected. Please check the CSS selectors.")
    print("="*60)
else:
    # Create DataFrame and save
    df = pd.DataFrame(data)
    
    # Remove duplicates based on URL
    initial_count = len(df)
    df = df.drop_duplicates(subset=['URL'], keep='first')
    duplicates_removed = initial_count - len(df)
    
    # Save using utils function
    save_raw_data(df, "brokeragebd_raw.csv")
    
    # Also save to the original location for compatibility
    output_path = r"E:\Cohor8\Capstone_1\dhaka_real_estate.csv"
    df.to_csv(output_path, index=False)
    
    print(f"\n{'='*60}")
    print(f"Scraping completed successfully!")
    print(f"{'='*60}")
    print(f"Total listings collected: {len(df)}")
    if duplicates_removed > 0:
        print(f"Duplicates removed: {duplicates_removed}")
    print(f"\nSaved to:")
    print(f"  - {output_path}")
    print(f"  - data/raw/brokeragebd_raw.csv")
    print(f"\n{'='*60}")
    print(f"Data summary:")
    print(f"{'='*60}")
    print(f"  - Records with Location: {df[df['Location'] != 'N/A'].shape[0]}")
    print(f"  - Records with Area_sqft: {df[df['Area_sqft'] != 'N/A'].shape[0]}")
    print(f"  - Records with Price: {df[df['Price'] != 'N/A'].shape[0]}")
    if "Price_BDT" in df.columns:
        print(f"  - Records with Price_BDT: {df[df['Price_BDT'] != 'N/A'].shape[0]}")
    print(f"  - Records with Bedroom: {df[df['Bedroom'] != 'N/A'].shape[0]}")
    print(f"  - Records with Bathroom: {df[df['Bathroom'] != 'N/A'].shape[0]}")
    print(f"  - Records with Floor: {df[df['Floor'] != 'N/A'].shape[0]}")
    print(f"  - Records with For (Rent/Sell): {df[df['For'] != 'N/A'].shape[0]}")
    print(f"  - Records with Property_Type: {df[df['Property_Type'] != 'N/A'].shape[0]}")
    print(f"  - Total URLs: {df['URL'].notna().sum()}")
    
    # Show breakdown by For (Rent/Sell)
    if 'For' in df.columns:
        print(f"\n  Breakdown by For (Rent/Sell):")
        for_breakdown = df[df['For'] != 'N/A']['For'].value_counts()
        for for_type, count in for_breakdown.items():
            print(f"    - {for_type}: {count}")
    print(f"\nFirst 5 records:")
    print(df.head().to_string())
    print(f"\n{'='*60}")
