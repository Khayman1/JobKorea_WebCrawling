import pandas as pd
from bs4 import BeautifulSoup
from requests import get
import time
from tqdm import tqdm

def extract_table_info(detail_soup):
    """
    상세페이지의 기업정보 테이블에서 label-value 딕셔너리를 추출.
    """
    info = {}
    trs = detail_soup.select("div.company-infomation-row.basic-infomation table tr")
    for tr in trs:
        th_tags = tr.find_all("th")
        td_tags = tr.find_all("td")
        for th, td in zip(th_tags, td_tags):
            label = th.get_text(strip=True)
            value = td.get_text(strip=True)
            info[label] = value
    return info

def get_jobkorea_data(corp_name_list, page_no=1):
    jobkorea_data = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    for corp_name in tqdm(corp_name_list, desc="기업정보 크롤링", unit="검색명"):
        url = f"https://www.jobkorea.co.kr/Search/?stext={corp_name}&tabType=corp&Page_No={page_no}"
        response = get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        flex_containers = soup.find_all(
            "div",
            class_="Flex_display_flex__i0l0hl2 Flex_direction_row__i0l0hl3 Flex_justify_space-between__i0l0hlf",
        )

        if not flex_containers:
            jobkorea_data.append({
                "검색어": corp_name,
                "기업명": "-",
                "기업형태": "-",
                "지역": "-",
                "업종": "-",
                "자본금": "-",
                "매출액": "-",
                "대표자": "-",
                "설립일": "-"
            })
            time.sleep(1.5)
            continue

        for container in flex_containers:
            # 기업명 추출 (a 태그 내부 bold span > 없으면 a 태그 텍스트)
            parent = container.find_parent(
                'div', 
                class_="Flex_display_flex__i0l0hl2 Flex_gap_space4__i0l0hly Flex_direction_column__i0l0hl4"
            )
            company_title = "-"
            if parent:
                a_tag = parent.find('a', href=True)
                if a_tag:
                    bold_span = a_tag.find("span", class_="Typography_weight_bold__344nw2b")
                    if bold_span:
                        company_title = bold_span.get_text(strip=True)
                    else:
                        company_title = a_tag.get_text(strip=True).split("\n")[0].strip()
            # 기업형태, 지역, 업종 추출
            inner_flex = container.find(
                "div",
                class_="Flex_display_flex__i0l0hl2 Flex_gap_space12__i0l0hls Flex_direction_row__i0l0hl3",
            )
            if not inner_flex:
                continue
            spans = inner_flex.find_all("span", class_="Typography_variant_size14__344nw27")
            if len(spans) == 3:
                corp_type, corp_location, corp_industry = (spans[0].get_text(strip=True),
                                                            spans[1].get_text(strip=True),
                                                            spans[2].get_text(strip=True))
            elif len(spans) == 4:
                corp_type, corp_location, corp_industry = (spans[1].get_text(strip=True),
                                                            spans[2].get_text(strip=True),
                                                            spans[3].get_text(strip=True))
            else:
                corp_type = corp_location = corp_industry = "-"

            # 상세페이지 이동하여 label-value 추출
            capital = sales = ceo = foundation_date = "-"
            if parent and a_tag:
                detail_response = get(a_tag['href'], headers=headers)
                detail_soup = BeautifulSoup(detail_response.text, "html.parser")
                info_dict = extract_table_info(detail_soup)
                capital = info_dict.get("자본금", "-")
                sales = info_dict.get("매출액", "-")
                ceo = info_dict.get("대표자", "-")
                foundation_date = info_dict.get("설립일", "-")

            # 결과 저장
            jobkorea_data.append({
                "검색어": corp_name,
                "기업명": company_title,
                "기업형태": corp_type or "-",
                "지역": corp_location or "-",
                "업종": corp_industry or "-",
                "자본금": capital or "-",
                "매출액": sales or "-",
                "대표자": ceo or "-",
                "설립일": foundation_date or "-"
            })
            time.sleep(1.5)  # 과도한 요청 방지

    return pd.DataFrame(jobkorea_data)

if __name__ == "__main__":
    corp_name_list = pd.read_csv("enterprise_df_14_utf8_data.csv")["기업명"].dropna().unique().tolist()
    result_df = get_jobkorea_data(corp_name_list)
    result_df.to_csv("jobkorea_data_14.csv", index=False, encoding="utf-8-sig")
    print("✅ 크롤링 완료! jobkorea_data_14.csv 저장됨.")
