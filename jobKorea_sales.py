import pandas as pd
from bs4 import BeautifulSoup
from requests import get
import time
from tqdm import tqdm

def get_jobkorea_data(corp_name_list, page_no=1):
    jobkorea_data = []
    headers = {
        # User-Agent로 브라우저처럼 요청
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    # tqdm으로 진행률 바 표시
    for corp_name in tqdm(corp_name_list, desc="기업정보 크롤링", unit="건"):
        capital = sales = ceo = foundation_date = None
        # 기업명으로 JobKorea 검색 페이지 요청
        url = f"https://www.jobkorea.co.kr/Search/?stext={corp_name}&tabType=corp&Page_No={page_no}"
        response = get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        # 검색 결과에서 기업 정보 컨테이너 찾기
        flex_containers = soup.find_all(
            "div",
            class_="Flex_display_flex__i0l0hl2 Flex_direction_row__i0l0hl3 Flex_justify_space-between__i0l0hlf",
        )

        found_company = False
        for container in flex_containers:
            # 컨테이너 내 상세 정보 추출
            inner_flex = container.find(
                "div",
                class_="Flex_display_flex__i0l0hl2 Flex_gap_space12__i0l0hls Flex_direction_row__i0l0hl3",
            )
            if not inner_flex:
                continue
            # 기업형태, 지역, 업종 span 추출
            spans = inner_flex.find_all("span", class_="Typography_variant_size14__344nw27")
            if len(spans) >= 3:
                found_company = True
                if len(spans) == 3:
                    corp_type, corp_location, corp_industry = (spans[0].get_text(strip=True),
                                                               spans[1].get_text(strip=True),
                                                               spans[2].get_text(strip=True))
                elif len(spans) == 4:
                    corp_type, corp_location, corp_industry = (spans[1].get_text(strip=True),
                                                               spans[2].get_text(strip=True),
                                                               spans[3].get_text(strip=True))
                # 상세페이지로 이동하여 세부정보 추출
                parent = container.find_parent('div', class_="Flex_display_flex__i0l0hl2 Flex_gap_space4__i0l0hly Flex_direction_column__i0l0hl4")
                if parent:
                    a_tag = parent.find('a', href=True)
                    if a_tag:
                        detail_response = get(a_tag['href'], headers=headers)
                        detail_soup = BeautifulSoup(detail_response.text, "html.parser")
                        # 자본금
                        value_container = detail_soup.select_one("div.company-infomation-row.basic-infomation > div > table > tbody > tr:nth-child(3) > td:nth-child(2) > div > div")
                        capital_tag = value_container.select_one(".value") if value_container else None
                        capital = capital_tag.text if capital_tag else ""
                        # 매출액
                        sales_container = detail_soup.select_one("div.company-infomation-row.basic-infomation > div > table > tbody > tr:nth-child(3) > td:nth-child(4) > div > div")
                        sales_tag = sales_container.select_one(".value") if sales_container else None
                        sales = sales_tag.text if sales_tag else ""
                        # 대표자
                        ceo_tag = detail_soup.select_one("div.company-infomation-row.basic-infomation > div > table > tbody > tr:nth-child(4) > td:nth-child(2) > div > div")
                        ceo = ceo_tag.text if ceo_tag else ""
                        # 설립일
                        foundation_date_tag = detail_soup.select_one("div.company-infomation-row.basic-infomation > div > table > tbody > tr:nth-child(2) > td:nth-child(4) > div > div > div.value")
                        foundation_date = foundation_date_tag.text if foundation_date_tag else ""
                # 결과 저장
                jobkorea_data.append({
                    "기업명": corp_name,
                    "기업형태": corp_type,
                    "지역": corp_location,
                    "업종": corp_industry,
                    "자본금": capital,
                    "매출액": sales,
                    "대표자": ceo,
                    "설립일": foundation_date
                })
                break  # 첫 번째 검색결과만 수집 후 break
        # 검색 결과가 없을 경우 빈 값 저장
        if not found_company:
            jobkorea_data.append({
                "기업명": corp_name,
                "기업형태": "",
                "지역": "",
                "업종": "",
                "자본금": "",
                "매출액": "",
                "대표자": "",
                "설립일": ""
            })
        time.sleep(1.5)  # 서버 부하 방지
    # 최종 DataFrame 반환
    return pd.DataFrame(jobkorea_data)

if __name__ == "__main__":
    # CSV에서 기업명 추출 (예: 담당 14번)
    corp_name_list = pd.read_csv("enterprise_df_14_utf8_data.csv")["기업명"].dropna().unique().tolist()
    # 크롤링 실행 및 결과 저장
    result_df = get_jobkorea_data(corp_name_list)
    result_df.to_csv("jobkorea_data_14.csv", index=False, encoding="utf-8-sig")
    print("✅ 크롤링 완료! jobkorea_data_14.csv 저장됨.")
