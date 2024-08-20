import sys
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import time


# Set up Chrome WebDriver options for headless browsing
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--disable-software-rasterizer')
options.add_argument('--disable-extensions')
options.add_argument('--disable-setuid-sandbox')
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)
options.add_argument('--js-flags=--max_old_space_size=4096')
restaurant_url = sys.argv[1]
# Initialize WebDriver
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(20)

# Open the specified restaurant page
restaurant_url = sys.argv[1]
driver.get(restaurant_url)
driver.maximize_window()

# Add a delay to allow the page to load completely
time.sleep(5)

# Initialize data structure
data = {
    "restaurant": {},
    "categories": []
}

try:
    # Scrape the rating value
    try:
        rating_value = driver.find_element(By.CSS_SELECTOR, 'span.sc-4114a3cc-2.hZTLxs').text
        data["restaurant"]["rating"] = rating_value
    except NoSuchElementException:
        data["restaurant"]["rating"] = "Not found"

    # Scrape the restaurant name
    try:
        restaurant_name = driver.find_element(By.CSS_SELECTOR, 'span.sc-1d8c3c90-5.yqJVW').text
        data["restaurant"]["name"] = restaurant_name
    except NoSuchElementException:
        data["restaurant"]["name"] = "Not found"

    # Scrape the address and postal code
    try:
        add_div = driver.find_element(By.CSS_SELECTOR, 'div.sc-347bbdf5-2.lfDeHN')
        p_elements = add_div.find_elements(By.CSS_SELECTOR, 'p.sc-347bbdf5-3.gXphZi')
        if len(p_elements) >= 2:
            data["restaurant"]["address"] = p_elements[0].text
            data["restaurant"]["postal_code"] = p_elements[1].text
        else:
            data["restaurant"]["address"] = "Not enough elements found"
            data["restaurant"]["postal_code"] = "Not enough elements found"
    except NoSuchElementException:
        data["restaurant"]["address"] = "Not found"
        data["restaurant"]["postal_code"] = "Not found"

    # Scrape the exact location
    try:
        location_url = driver.find_element(By.CSS_SELECTOR, 'a.sc-347bbdf5-4.bVTPXr').get_attribute('href')
        data["restaurant"]["location_url"] = location_url
    except NoSuchElementException:
        data["restaurant"]["location_url"] = "Not found"

    # Scrape the phone number
    try:
        phone_div = driver.find_element(By.CSS_SELECTOR, 'div.sc-17dd534d-2.jVbAbK')
        phone_number = phone_div.find_element(By.CSS_SELECTOR, 'a.sc-d3897b5b-0.hxQBJs').text
        data["restaurant"]["phone_number"] = phone_number
    except NoSuchElementException:
        data["restaurant"]["phone_number"] = "Not found"
    
    # Locate all divs with the class sc-c2fb129f-0 dEeFMI for categories and products
    container_divs = driver.find_elements(By.CSS_SELECTOR, 'div.sc-c2fb129f-0.dEeFMI')
    for container in container_divs:
        try:
            # Scrape the category name within the current div
            category_name = container.find_element(By.CSS_SELECTOR, 'h2.sc-8a851f37-2.gTEQrl').text
            category = {
                "category_name": category_name,
                "products": []
            }

            # Find all product divs within the current category div
            products = container.find_elements(By.CSS_SELECTOR, 'div.sc-d1b749f8-11.ipCGgH')
            for index in range(len(products)):
                try:
                    product = products[index]
                    driver.execute_script("arguments[0].scrollIntoView(true);", product)

                    # Get product title
                    product_title = product.find_element(By.CSS_SELECTOR, 'h3.sc-b8b0ebaa-2.kUWsgy').text
                    product_data = {
                        "title": product_title,
                        "description": "No description available",
                        "price": "Not found",
                        "image_url": "Not found",
                        "extras": []
                    }

                    # Get product description (if exists)
                    try:
                        product_description = product.find_element(By.CSS_SELECTOR, 'p.sc-b8b0ebaa-0.bbgpLq').text
                        product_data["description"] = product_description
                    except NoSuchElementException:
                        pass

                    # Get product price
                    try:
                        product_price = product.find_element(By.CSS_SELECTOR, 'span.sc-51a42e35-3.czgNUi, span.sc-51a42e35-4.bmWCtt').text

                        product_data["price"] = product_price
                    except NoSuchElementException:
                        pass

                    # Get product image URL
                    try:
                        image_div = product.find_element(By.CSS_SELECTOR, 'div.sc-d1b749f8-5.XJRoo')
                        product_image = image_div.find_element(By.CSS_SELECTOR, 'img.s1siin91').get_attribute('src')
                        product_data["image_url"] = product_image
                    except NoSuchElementException:
                        pass

                    # Open modal to scrape additional details
                    try:
                        modal_button = product.find_element(By.CSS_SELECTOR, 'button.sc-d1b749f8-1.jwPFQd')
                        driver.execute_script("arguments[0].click();", modal_button)
                        WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, 'form.sc-afaf3dbf-11.jPyLVb'))
                        )

                        # Scrape modal details
                        form = driver.find_element(By.CSS_SELECTOR, 'form.sc-afaf3dbf-11.jPyLVb')
                        extras_divs = form.find_elements(By.CSS_SELECTOR, 'div.sc-afaf3dbf-0.hiNunn')
                        for extra_div in extras_divs:
                            extras_type = extra_div.find_element(By.CSS_SELECTOR, 'legend.sc-afaf3dbf-7.dSiawP').text
                            print(f"Extras Type: {extras_type}")
                            extra_items=[]
                            labels = extra_div.find_elements(By.CSS_SELECTOR, 'div.sc-afaf3dbf-9.fHQSmp label')
                            for label in labels:
                                try:
                                    extras_name = label.find_element(By.CSS_SELECTOR, 'span.sc-884f547b-1.ivyrED').text
                                except NoSuchElementException:
                                    extras_name = "No name available"
                                print(f"Extras Name: {extras_name}")

                                try:
                                    extras_price = label.find_element(By.CSS_SELECTOR, 'span.sc-104eb88-1.hGItFl').text
                                    # extras_price = extras_price.replace('\u20ac', '€')
                                except NoSuchElementException:
                                    extras_price = "free"
                                print(f"Extras Price: {extras_price}")
                                print("-" * 40)
                                extra_items.append({
                                    "name": extras_name,
                                    "price": extras_price
                                })
                            product_data["extras"].append({
                                "type": extras_type,
                                "items": extra_items
                            })

                        # Close modal
                        close_button = driver.find_element(By.CSS_SELECTOR, 'button.cb_IconButton_root_r1x5')
                        driver.execute_script("arguments[0].click();", close_button)
                        time.sleep(2)  # Wait for modal to close
                    except (NoSuchElementException, TimeoutException):
                        pass

                    # Append product data to category
                    category["products"].append(product_data)

                except (NoSuchElementException, StaleElementReferenceException):
                    continue

            # Append category data to main data
            data["categories"].append(category)

        except NoSuchElementException:
            continue

except TimeoutException:
    pass  # Handle timeout if needed

finally:
    # Print data in JSON format
    print(json.dumps(data, indent=4))

    # Store data in a JSON file
    with open('scraped_data.json', 'w', encoding='utf-8') as file:
       json.dump(data, file, indent=4, ensure_ascii=False)


    driver.quit()