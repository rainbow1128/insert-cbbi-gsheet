import requests
from datetime import datetime, timedelta
from itertools import islice
import gspread
from gspread.exceptions import SpreadsheetNotFound, APIError, GSpreadException
import json, os, base64


def fetch_json_data(url):
    # Set the headers to accept JSON
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        json_data = response.json()
        if json_data:
            data = json_data["Confidence"]
            converted_data = {
                (datetime.fromtimestamp(int(timestamp)) + timedelta(days=1)).strftime(
                    "%Y-%m-%d"
                ): str(value * 100)
                for timestamp, value in data.items()
            }

            sorted_data = {
                date: event
                for date, event in sorted(converted_data.items(), reverse=True)
            }

            final_data = dict(islice(sorted_data.items(), 30))

        return final_data
    else:
        print("Failed to retrieve data. Status code:", response.status_code)
        return None


def authenticate_gspread():
    json_credentials = os.getenv("CREDENTIAL")
    credentials_dict = json.loads(base64.b64decode(json_credentials).decode("utf-8"))
    gc = gspread.service_account_info(credentials_dict)
    # gc = gspread.service_account(filename=json_credentials_path)
    return gc


def insert_data(sheet_url, data, worksheet_index=0):
    """Insert data into a Google Sheet."""
    try:

        gc = authenticate_gspread()
        sh = gc.open_by_url(sheet_url)

        worksheet = sh.get_worksheet(worksheet_index)
        worksheet.clear()
        worksheet.append_row(["Data", "CBBI"])
        rows = [[key, value] for key, value in data.items()]
        worksheet.append_rows(rows)
        print("Data successfully written to the sheet.")

    except SpreadsheetNotFound:
        print("The specified Google Sheet was not found.")
    except APIError as e:
        print(f"An API error occurred: {e}")
    except GSpreadException as e:
        print(f"A gspread exception occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def main(url, sheet_url):
    data = fetch_json_data(url)
    if data:
        insert_data(sheet_url, data)


url = "https://colintalkscrypto.com/cbbi/data/latest.json"
sheet_url = os.getenv("GOOGLE_SHEET_URL")
main(url, sheet_url)
