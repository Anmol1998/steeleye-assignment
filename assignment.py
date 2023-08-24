import requests
import json
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(filename)s:%(lineno)d] %(levelname)s - %(message)s",
    datefmt="%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# api-endpoints
LAUREATE_URL = "http://api.nobelprize.org/v1/laureate.json"
COUNTRY_URL = "http://api.nobelprize.org/v1/country.json"


def get_api_data(URL):
    r = requests.get(url=URL, verify=False)
    data = r.json()
    return data


try:
    laureate_data = get_api_data(LAUREATE_URL)
    country_data = get_api_data(COUNTRY_URL)

    df_laureates = pd.json_normalize(laureate_data["laureates"])[
        ["id", "firstname", "surname", "gender", "bornCountryCode", "born"]
    ]

    df_countries = pd.json_normalize(country_data["countries"])
    df_countries.rename(columns={"name": "country_name"}, inplace=True)

    # drop duplicates from df_countries
    df_countries.drop_duplicates(subset=["code"], inplace=True)

    # create new df for prize year and category
    df_prizes = pd.DataFrame(columns=["id", "year", "category"])

    # unnest json to extract required data
    for i in laureate_data["laureates"]:
        id = i["id"]
        yr = i["prizes"][0]["year"]
        category = i["prizes"][0]["category"]
        if len(i["prizes"]) > 1:
            for j in i["prizes"][1:]:
                yr = yr + "; " + j["year"]
                category = category + "; " + j["category"]
        df_prizes.loc[len(df_prizes.index)] = [id, yr, category]

    df_laureates_country = pd.merge(
        df_laureates,
        df_countries,
        left_on="bornCountryCode",
        right_on="code",
        how="left",
    )

    df_final = pd.merge(
        df_laureates_country,
        df_prizes,
        on="id",
        how="left",
    )

    # concat firstname and surname
    surname = df_final["surname"].copy()

    # string to replace null values with
    na_string = ""

    df_final["name"] = df_final["firstname"].str.cat(surname, sep=" ", na_rep=na_string)

    print(df_final.head())

    # rename columns as per requirement
    df_final.rename(
        columns={
            "born": "dob",
            "year": "unique_prize_years",
            "category": "unique_prize_categories",
        },
        inplace=True,
    )

    df_final.to_csv(
        "merged_file.csv",
        columns=[
            "id",
            "name",
            "dob",
            "unique_prize_years",
            "unique_prize_categories",
            "gender",
            "country_name",
        ],
        index=False,
    )

except Exception as e:
    logger.error(str(e))
