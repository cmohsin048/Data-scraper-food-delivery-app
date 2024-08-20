
# pip install Flask selenium
# python Apiscraper.py




from flask import Flask, request, jsonify, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import time
import json
import os
import tempfile
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)

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

@app.route('/scrape', methods=['POST'])
def scrape():
    # Get URL from request
    url_data = request.json
    restaurant_url = url_data.get("url")

    if not restaurant_url:
        return jsonify({"error": "URL is required"}), 400

    # Initialize WebDriver
    driver = None
    temp_file_path = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(20)

        # Open the specified restaurant page
        driver.get(restaurant_url)
        time.sleep(5)

        # Initialize data structure
        data = {
            "restaurant": {},
            "categories": []
        }

        # Scrape data as before
        try:
            rating_value = driver.find_element(By.CSS_SELECTOR, 'span.sc-4114a3cc-2.hZTLxs').text
            data["restaurant"]["rating"] = rating_value
        except NoSuchElementException:
            data["restaurant"]["rating"] = "Not found"

        try:
            restaurant_name = driver.find_element(By.CSS_SELECTOR, 'span.sc-1d8c3c90-5.yqJVW').text
            data["restaurant"]["name"] = restaurant_name
        except NoSuchElementException:
            data["restaurant"]["name"] = "Not found"

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

        try:
            location_url = driver.find_element(By.CSS_SELECTOR, 'a.sc-347bbdf5-4.bVTPXr').get_attribute('href')
            data["restaurant"]["location_url"] = location_url
        except NoSuchElementException:
            data["restaurant"]["location_url"] = "Not found"

        try:
            phone_div = driver.find_element(By.CSS_SELECTOR, 'div.sc-17dd534d-2.jVbAbK')
            phone_number = phone_div.find_element(By.CSS_SELECTOR, 'a.sc-d3897b5b-0.hxQBJs').text
            data["restaurant"]["phone_number"] = phone_number
        except NoSuchElementException:
            data["restaurant"]["phone_number"] = "Not found"

        container_divs = driver.find_elements(By.CSS_SELECTOR, 'div.sc-c2fb129f-0.dEeFMI')
        for container in container_divs:
            try:
                category_name = container.find_element(By.CSS_SELECTOR, 'h2.sc-8a851f37-2.gTEQrl').text
                category = {
                    "category_name": category_name,
                    "products": []
                }

                products = container.find_elements(By.CSS_SELECTOR, 'div.sc-d1b749f8-11.ipCGgH')
                for index in range(len(products)):
                    try:
                        product = products[index]
                        driver.execute_script("arguments[0].scrollIntoView(true);", product)

                        product_title = product.find_element(By.CSS_SELECTOR, 'h3.sc-b8b0ebaa-2.kUWsgy').text
                        product_data = {
                            "title": product_title,
                            "description": "No description available",
                            "price": "Not found",
                            "image_url": "Not found",
                            "extras": []
                        }
                        try:
                            product_description = product.find_element(By.CSS_SELECTOR, 'p.sc-b8b0ebaa-0.bbgpLq').text
                            product_data["description"] = product_description
                        except NoSuchElementException:
                            pass
                        try:
                            product_price = product.find_element(By.CSS_SELECTOR, 'span.sc-51a42e35-3.czgNUi, span.sc-51a42e35-4.bmWCtt').text
                            product_data["price"] = product_price
                        except NoSuchElementException:
                            pass
                        try:
                            image_div = product.find_element(By.CSS_SELECTOR, 'div.sc-d1b749f8-5.XJRoo')
                            product_image = image_div.find_element(By.CSS_SELECTOR, 'img.s1siin91').get_attribute('src')
                            product_data["image_url"] = product_image
                        except NoSuchElementException:
                            pass
                        try:
                            modal_button = product.find_element(By.CSS_SELECTOR, 'button.sc-d1b749f8-1.jwPFQd')
                            driver.execute_script("arguments[0].click();", modal_button)
                            WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, 'form.sc-afaf3dbf-11.jPyLVb'))
                            )
                            form = driver.find_element(By.CSS_SELECTOR, 'form.sc-afaf3dbf-11.jPyLVb')
                            extras_divs = form.find_elements(By.CSS_SELECTOR, 'div.sc-afaf3dbf-0.hiNunn')
                            for extra_div in extras_divs:
                                extras_type = extra_div.find_element(By.CSS_SELECTOR, 'legend.sc-afaf3dbf-7.dSiawP').text
                                extra_items = []
                                labels = extra_div.find_elements(By.CSS_SELECTOR, 'div.sc-afaf3dbf-9.fHQSmp label')
                                for label in labels:
                                    try:
                                        extras_name = label.find_element(By.CSS_SELECTOR, 'span.sc-884f547b-1.ivyrED').text
                                    except NoSuchElementException:
                                        extras_name = "No name available"

                                    try:
                                        extras_price = label.find_element(By.CSS_SELECTOR, 'span.sc-104eb88-1.hGItFl').text
                                    except NoSuchElementException:
                                        extras_price = "free"

                                    extra_items.append({
                                        "name": extras_name,
                                        "price": extras_price
                                    })
                                product_data["extras"].append({
                                    "type": extras_type,
                                    "items": extra_items
                                })
                            close_button = driver.find_element(By.CSS_SELECTOR, 'button.cb_IconButton_root_r1x5')
                            driver.execute_script("arguments[0].click();", close_button)
                            time.sleep(2)  # Wait for modal to close
                        except (NoSuchElementException, TimeoutException):
                            pass
                        category["products"].append(product_data)
                    except (NoSuchElementException, StaleElementReferenceException):
                        continue
                data["categories"].append(category)
            except NoSuchElementException:
                continue
        # Save data to a temporary JSON file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8')
        temp_file_path = temp_file.name
        with open(temp_file_path, 'w',encoding='utf-8') as f:
            json.dump(data, f, indent=4,ensure_ascii=False)
        temp_file.close()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return jsonify({"error": "An error occurred during scraping"}), 500

    finally:
        if driver:
            driver.quit()

    # Send the JSON file as a response
    if temp_file_path and os.path.exists(temp_file_path):
        return send_file(temp_file_path, as_attachment=True, download_name='scraped_data.json')
    else:
    # Save data to a file if temp_file_path does not exist
        with open('scraped_data.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        if os.path.exists('scraped_data.json'):
            return send_file('scraped_data.json', as_attachment=True, download_name='scraped_data.json')
    
# If none of the conditions were met
    return jsonify({"error": "Failed to generate the JSON file"}), 500


if __name__ == '__main__':
    app.run(debug=True)
