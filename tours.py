import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import re

def extract_card_info(card):
    """Trích xuất thông tin cơ bản từ trang danh sách."""
    name_tag = card.find("h2")
    name = name_tag.get_text(strip=True) if name_tag else "Không có tên"

    price_tag = card.find("span", class_="tourItemPrice")
    price = price_tag.get_text(strip=True) if price_tag else "Liên hệ"

    date_pattern = re.compile(r'\d{2}-\d{2}-\d{4}')
    date_tag = card.find("span", class_="tourItemDateTime")
    date = date_pattern.search(date_tag.get_text()).group() if date_tag and date_pattern.search(date_tag.get_text()) else "Không có ngày"

    return {"name": name, "price": price, "date": date}

def extract_detail_info(detail_url):
    """Trích xuất thông tin chi tiết từ trang tour."""
    response = requests.get(detail_url)
    soup = BeautifulSoup(response.content, "html.parser")

    name_tag = soup.find("h1")
    name = name_tag.get_text(strip=True) if name_tag else "Không có tên"

    review_section = soup.find("div", class_="tourSchedule")
    reviews = [p.get_text(strip=True) for p in review_section.find_all("p")] if review_section else []
    overview = " ".join(reviews)

    img_tag = soup.find("img", class_="avatar-small")
    if img_tag and "src" in img_tag.attrs:
        image_url = img_tag["src"]
        image = f"https:{image_url}" if image_url.startswith("//") else image_url  # Thêm "https:" nếu cần
    else:
        image = "Không tìm thấy ảnh"

    return {"name": name, "overview": overview, "image": image}

def scrape_tour_data(base_url, links):
    """Thu thập dữ liệu từ danh sách tour và trang chi tiết."""
    tours = []
    for link in links:
        url = f"{base_url}{link}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Tìm tất cả các thẻ card
        cards = soup.find_all("div", class_="tourItemContent")

        # Tìm tất cả link chi tiết
        detail_link_tags = soup.find_all("a", class_="linkDetail")
        detail_links = [f"{base_url}{a['href']}" for a in detail_link_tags if "href" in a.attrs]

        tour_data = []  # Lưu danh sách các tour

        # Vòng lặp qua danh sách cards
        for card in cards:
            tour_info = extract_card_info(card)
            tour_data.append(tour_info)  # Lưu lại thông tin cơ bản

        # Vòng lặp qua danh sách chi tiết
        for detail_link in detail_links:
            detail_info = extract_detail_info(detail_link)

            # So sánh name để cập nhật thông tin chi tiết
            for tour in tour_data:
                if tour["name"] == detail_info["name"]:
                    tour.update(detail_info)

        tours.extend(tour_data)  # Thêm tất cả dữ liệu đã ghép vào danh sách chính

    return tours

# Đọc danh sách đường dẫn từ file JSON
des = pd.read_json("destination.json")
links = des["Link"]
base_url = "https://www.ivivu.com"

# Thu thập dữ liệu
tours = scrape_tour_data(base_url, links)

# Lưu vào file CSV
csv_file = "tours_data.csv"
with open(csv_file, mode="w", newline="", encoding="utf-8-sig") as file:
    fieldnames = ["name", "price", "date", "overview", "image"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(tours)

print(f"Dữ liệu đã được lưu vào {csv_file}")
