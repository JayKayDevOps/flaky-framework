import random
import time
import pytest
import pandas as pd
import matplotlib.pyplot as plt
from playwright.sync_api import sync_playwright

# File to store test results
LOG_FILE = "test_results.csv"

# Mock data: List of test cases (URLs and expected HTTP status)
MOCK_DATA = [
    ("https://example.com", 200),
    ("https://playwright.dev", 200),
]

# Ensure CSV file is initialized (create an empty file)
with open(LOG_FILE, "w") as f:
    f.write("timestamp,url,passed,status\n")  # Write CSV header


@pytest.fixture(scope="session")
def browser():
    """Fixture to initialize and close a Playwright browser instance."""
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

    # Simulating a flaky test with an 80% pass rate
    test_passed = random.random() < 0.8  # 80% chance of success
    status_code = expected_status if test_passed else 500  # 500 for simulated failures

    # Log test result (timestamp, URL, pass/fail, status)
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.time()},{url},{test_passed},{status_code}\n")

    # Assert that test passes (this introduces the flakiness)
    assert test_passed, f"Test failed for {url} with status {status_code}"


def generate_report():
    """
    Reads the test results from the CSV file and generates a bar graph
    showing the number of passed vs. failed test cases for each URL.
    """
    try:
        df = pd.read_csv(LOG_FILE)  # Read test results CSV
        pass_fail_counts = df.groupby("url")["passed"].value_counts().unstack(fill_value=0)

        # Plot test results as a stacked bar graph
        pass_fail_counts.plot(kind="bar", stacked=True, colormap="coolwarm")
        plt.xlabel("Test URL")
        plt.ylabel("Test Count")
        plt.title("Flaky Test Results Over 100 Runs")
        plt.legend(["Failed", "Passed"])

        # Save the graph as an image
        plt.savefig("test_report.png")
        print("Report generated: test_report.png")
    except Exception as e:
        print(f"Error generating report: {e}")


if __name__ == "__main__":
    generate_report()  # Run report generation when executed directly
