import csv
from decimal import Decimal

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# TODO: move to another file
class Drone:

    def __init__(self, prod_id=0, brand='', title='', price=Decimal(0.00), reviews=0, stars=0.0):
        self.prod_id = prod_id
        self.brand = brand
        self.title = title
        self.price = price
        self.reviews = reviews
        self.stars = stars

    def __str__(self):
        return f"\n[[{self.prod_id, self.title}]]\n"

    def __iter__(self):
        return iter([self.prod_id, self.brand, self.title, self.price, self.reviews, self.stars])


class Scraper:

    def __init__(self, debug=False):
        self.debug = debug
        self.products = []

        # Selectors
        self._prod_id_selector = 'div.reviewer-id'
        self._product_list_selector = 'ul.goodlist.cf > li > div.p-wrap > a.title'
        self._next_button_selector = 'a.iconfont.icon-arrow_right_new1.btn-page.next-page'
        self._title_selector = 'span.product-title-text'
        self._brand_selector = 'div.reviewer-brand > a'
        self._price_selector = 'span.main-price'
        self._reviews_selector = 'span.rating-num.J-rating-num > span.reviews-num'
        self._stars_selector = 'div.reviewer-rating > span.star-num.js-star-num'

        # Vars
        self.elem_wait = 10
        self._driver = None
        self._product_urls = []

    def scrape(self, root_url, min_prod_count):
        self._init_driver()
        self._product_urls = self._get_product_url_list(root_url, min_prod_count)
        self.products = self._get_product_from_url_list(self._product_urls)
        self._close_driver()
        print(f'Scraping done!')
        print(f'Got {len(self.products)} products out of {len(self._product_urls)} links.')
        print(f'Closing scraper.')

    def _init_driver(self):
        print('Loading web driver...')
        if self._driver is None:
            options = Options()
            if not self.debug:
                options.headless = True
            self._driver = webdriver.Chrome(executable_path='chromedriver', options=options)
            print('Driver loaded!')
        else:
            print("Driver is already loaded!")

    def _close_driver(self):
        print("Closing driver...")
        self._driver.quit()
        self._driver = None
        print("Driver closed !")

    def _get_product_url_list(self, base_url, min_prod_count):
        print(f"Gathering at least {min_prod_count} product links...")

        # Initial vars
        product_url_list = []
        next_page_url = ''

        # Go through product listings until min product count is reached
        while len(product_url_list) < min_prod_count:
            if next_page_url == '':
                # Navigate to page
                self._driver.get(base_url)
                if self.debug:
                    print(base_url)
            else:
                # Navigate to next page
                self._driver.get(next_page_url)
                if self.debug:
                    print(next_page_url)

            # Wait for products to render on page
            self._wait_product_list_render()

            # Get all urls to the products on this page
            print('Grabbing all products on current page.')
            prod_list = self._driver.find_elements(By.CSS_SELECTOR, self._product_list_selector)
            for prod_url in prod_list:
                product_url_list.append(prod_url.get_attribute('href'))
                if self.debug:
                    # print last url
                    print(product_url_list[-1])

            print(f"Processed {len(product_url_list)} product links out of the {min_prod_count} required.")

            # Get url for next page
            next_page_url = self._driver.find_element(By.CSS_SELECTOR, self._next_button_selector).get_attribute('href')

        print("Product links scraping done!")

        # Return product url list
        return product_url_list[:min_prod_count]

    def _get_product_from_url_list(self, product_urls):
        print(f"Gathering product information from the {len(self._product_urls)} scrapped links...")

        # Initial vars
        drones = []

        # Go through each product
        for i, product_url in enumerate(product_urls):
            try:
                # Load the url of the product
                self._driver.get(product_url)
                # Wait for the required elements to render
                self._wait_product_page_render()

                # Scrape information from page
                # Add new drone with scraped info to list
                drones.append(
                    Drone(
                        prod_id=int(self._scrap_elem(self._prod_id_selector)[4:]),
                        brand=self._scrap_elem(self._brand_selector),
                        title=self._scrap_elem(self._title_selector),
                        price=Decimal(
                            "".join(
                                d for d in self._scrap_elem(self._price_selector)
                                if d.isdigit() or d == '.'
                            )
                        ),
                        reviews=int(self._scrap_elem(self._reviews_selector)),
                        stars=float(self._scrap_elem(self._stars_selector))
                    )
                )
                print(drones[-1])
                print(f"Product {i} out of {len(self._product_urls)} scraped: Success...")
            except Exception as e:
                if self.debug:
                    print(e)
                print(f"Product {i} out of {len(self._product_urls)} scraped: FAIL...")
                self._close_driver()
                self._init_driver()

        return drones

    def _wait_product_page_render(self):
        WebDriverWait(self._driver, self.elem_wait) \
            .until(EC.visibility_of_element_located((By.CSS_SELECTOR, self._title_selector)))
        WebDriverWait(self._driver, self.elem_wait) \
            .until(EC.visibility_of_element_located((By.CSS_SELECTOR, self._brand_selector)))
        WebDriverWait(self._driver, self.elem_wait) \
            .until(EC.visibility_of_element_located((By.CSS_SELECTOR, self._price_selector)))
        WebDriverWait(self._driver, self.elem_wait) \
            .until(EC.visibility_of_element_located((By.CSS_SELECTOR, self._reviews_selector)))
        WebDriverWait(self._driver, self.elem_wait) \
            .until(EC.visibility_of_element_located((By.CSS_SELECTOR, self._stars_selector)))

    def _wait_product_list_render(self):
        WebDriverWait(self._driver, self.elem_wait) \
            .until(EC.visibility_of_element_located((By.CSS_SELECTOR, self._product_list_selector)))

    def _scrap_elem(self, css_selector, raw=False):
        elem = self._driver.find_element(By.CSS_SELECTOR, css_selector)

        if raw:
            return elem
        else:
            return elem.text


scrapper = Scraper(debug=True)
scrapper.scrape("https://www.banggood.com/Wholesale-RC-Drones-c-8767.html", 500)


#from another class
with open('products.csv', 'w') as csv_file:
    wr = csv.writer(csv_file, delimiter=',')
    for drone in scrapper.products:
        #if drone.id not in existing_ids
        wr.writerow(list(drone))

