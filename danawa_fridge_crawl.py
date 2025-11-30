import csv
import re
import time
from typing import List, Tuple, Optional

from bs4 import BeautifulSoup
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


START_URL = "https://prod.danawa.com/list/?cate=102110"
OUTPUT_CSV = "danawa_fridge_capacity.csv"
MAX_PAGES = 200  # 안전장치용 상한


# -------------------------------
#  스펙 파싱: 총용량 / 냉장 / 냉동
# -------------------------------
def extract_capacities(spec_text: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    스펙 문자열에서 총용량, 냉장, 냉동 용량(L) 추출
    예) '... 총용량: 870L/냉장: 503L/냉동: 367L/...'
    """
    def find_l(pattern: str) -> Optional[int]:
        m = re.search(pattern, spec_text)
        if not m:
            return None
        return int(m.group(1).replace(",", ""))

    total_l = find_l(r"총용량\s*:?\s*([\d,]+)\s*L")
    fridge_l = find_l(r"냉장\s*:?\s*([\d,]+)\s*L")
    freezer_l = find_l(r"냉동\s*:?\s*([\d,]+)\s*L")

    return total_l, fridge_l, freezer_l


# -------------------------------
#  현재 페이지에서 상품 정보 추출
# -------------------------------
def parse_current_page(driver) -> List[Tuple[str, int, int, int]]:
    """
    현재 페이지 HTML에서 (제품명, 총용량, 냉동, 냉장) 리스트 추출
    반환: [(name, total_l, freezer_l, fridge_l), ...]
    """
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    items = soup.select("li.prod_item.prod_layer")

    results: List[Tuple[str, int, int, int]] = []

    for item in items:
        name_el = item.select_one("p.prod_name > a")
        if not name_el:
            continue
        name = name_el.get_text(" ", strip=True)

        spec_el = item.select_one("div.spec_list")
        if spec_el is None:
            spec_el = item.select_one("div.prod_spec_set")
        if spec_el is None:
            continue

        spec_text = spec_el.get_text(" ", strip=True)

        total_l, fridge_l, freezer_l = extract_capacities(spec_text)
        if total_l is None or fridge_l is None or freezer_l is None:
            # 세 값 다 있을 때만
            continue

        results.append((name, total_l, freezer_l, fridge_l))

    return results


# -------------------------------
#  다음 페이지 이동 로직
# -------------------------------
def go_to_next_page(driver, current_page: int) -> bool:
    """
    1순위: 현재 페이지 + 1 숫자 링크 클릭
    2순위: 숫자 링크가 없으면 '다음 페이지'(a.edge_nav.nav_next) 클릭

    성공하면 True, 더 이상 진행 불가하면 False
    """
    next_num = current_page + 1
    next_str = str(next_num)

    # 1) 숫자 페이지 링크 시도
    try:
        # class 안에 "num"이 포함되고 텍스트가 next_str인 a 태그
        locator = (
            By.XPATH,
            f'//a[contains(@class, "num") and normalize-space()="{next_str}"]'
        )
        next_link = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable(locator)
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", next_link)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", next_link)
        time.sleep(2)
        print(f"  → 숫자 페이지 {next_str} 링크 클릭")
        return True

    except TimeoutException:
        print(f"  숫자 {next_str} 링크가 보이지 않습니다. '다음 페이지' 버튼을 시도합니다.")

    # 2) '다음 페이지' 버튼 시도
    try:
        locator = (By.CSS_SELECTOR, "a.edge_nav.nav_next")
        next_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable(locator)
        )

        class_attr = next_btn.get_attribute("class") or ""
        if "disabled" in class_attr or "off" in class_attr:
            print("  '다음 페이지' 버튼이 비활성입니다. 마지막 페이지로 판단합니다.")
            return False

        driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", next_btn)
        time.sleep(2)
        print("  → '다음 페이지' 버튼 클릭")
        return True

    except TimeoutException:
        print("  '다음 페이지' 버튼도 찾지 못했습니다. 더 이상 진행할 수 없습니다.")
        return False


# -------------------------------
#  메인 루프
# -------------------------------
def main():
    chromedriver_autoinstaller.install()

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")        # 창 안 띄우고 실행
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)

    driver.get(START_URL)
    time.sleep(3)

    all_rows: List[Tuple[str, int, int, int]] = []
    current_page = 1

    while current_page <= MAX_PAGES:
        print(f"\n===== {current_page} 페이지 크롤링 중 =====")

        page_rows = parse_current_page(driver)
        print(f"  → {len(page_rows)}개 추출")
        all_rows.extend(page_rows)

        # 다음 페이지로 이동 시도
        if not go_to_next_page(driver, current_page):
            break

        current_page += 1

    driver.quit()

    print(f"\n총 {len(all_rows)}개 상품을 CSV로 저장합니다: {OUTPUT_CSV}")
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["제품명", "총용량(L)", "냉동(L)", "냉장(L)"])
        writer.writerows(all_rows)


if __name__ == "__main__":
    main()
