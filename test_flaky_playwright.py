import random
import time
import pytest
import pandas as pd
import matplotlib.pyplot as plt
from playwright.sync_api import sync_playwright
import os

# Ensure output directory exists
OUTPUT_DIR = "artifacts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define file paths for results and report
LOG_FILE = os.path.join(OUTPUT_DIR, "test_results.csv")
REPORT_FILE = os.path.join(OUTPUT_DIR, "test_report.png")

# Mock data: List of test cases (URLs and expected HTTP status)
MOCK_DATA = [
    ("https://elverys.ie", 200),
    ("https://www.lifestylesports.com", 200),
    ("https://bbc.co.uk", 200),
    ("https://rte.ie", 200),
    ("https://www.jdsports.ie", 200),
    ("https://duke.edu", 200),
    ("https://sportsdirect.com", 200),
    ("https://www.prodirectsport.com", 200),
    ("https://www.nike.com", 200),   
    ("https://www.crocs.eu", 200)
]

# Ensure CSV file is initialized with headers
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        f.write("timestamp,url,passed,status\n")


@pytest.fixture(scope="session")
def browser():
    """Initialize and close a Playwright browser instance."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.mark.parametrize("url,expected_status", MOCK_DATA * 5)  # 10 test cases
def test_flaky_page(browser, url, expected_status):
    """
    Simulates a flaky test by introducing random failures.
    - 80% chance of passing
    - 20% chance of failing (randomly returns a 500 status)
    - Logs results to a CSV file
    """
    page = browser.new_page()
    page.goto(url)
    time.sleep(random.uniform(0.1, 0.5))  # Simulate variable load time

    test_passed = random.random() < 0.8  # 80% chance of success
    status_code = expected_status if test_passed else 500  # 500 for simulated failures

    # Log test result (timestamp, URL, pass/fail, status)
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.time()},{url},{int(test_passed)},{status_code}\n")  # Ensure 'passed' is int (1/0)

    assert test_passed, f"Test failed for {url} with status {status_code}"


def generate_report():
    """
    Reads test results and generates a bar graph
    showing the number of passed vs. failed test cases.
    """
    try:
        # Read CSV with proper data type conversion
        df = pd.read_csv(LOG_FILE)

        if df.empty:
            raise ValueError("❌ CSV file is empty. No data to plot.")

        # Convert columns to correct types
        df["passed"] = df["passed"].astype(int)  # Ensure passed is numeric
        df["status"] = df["status"].astype(int)  # Ensure status is numeric

        # Group by URL and count pass/fail occurrences
        pass_fail_counts = df.groupby("url")["passed"].value_counts().unstack(fill_value=0)

        # Plot test results as a stacked bar graph
        pass_fail_counts.plot(kind="bar", stacked=True, color=["green", "red"])
        plt.xlabel("Test URL")
        plt.ylabel("Test Count")
        plt.title("Flaky Test Results Over 100 Runs")
        plt.legend(["Failed", "Passed"])

        # Save the graph
        plt.savefig(REPORT_FILE)
        print(f"✅ Report generated: {REPORT_FILE}")

    except Exception as e:
        print(f"❌ Error generating report: {e}")
        print("🔎 Debugging CSV contents:")
        try:
            print(pd.read_csv(LOG_FILE).head())  # Print first few rows for debugging
        except Exception as debug_e:
            print(f"⚠️ Failed to read CSV: {debug_e}")


if __name__ == "__main__":
    generate_report()
