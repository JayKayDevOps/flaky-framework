import random
import time
import pytest
import pandas as pd
import matplotlib.pyplot as plt
from playwright.sync_api import sync_playwright
import os
from collections import defaultdict

# Ensure output directory exists
OUTPUT_DIR = "artifacts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define file paths for results and reports
LOG_FILE = os.path.join(OUTPUT_DIR, "test_results.csv")
REPORT_FILE = os.path.join(OUTPUT_DIR, "test_report.png")
FLAKY_REPORT_FILE = os.path.join(OUTPUT_DIR, "flaky_tests_report.png")
FLAKY_TESTS_FILE = os.path.join(OUTPUT_DIR, "flaky_tests.csv")

# Mock data: List of test cases (URLs and expected HTTP status)
MOCK_DATA = [
    ("https://elverys.ie", 200),
    ("https://www.lifestylesports.com", 200),
    ("https://bbc.co.uk", 200),
    ("https://rte.ie", 200),
    ("https://www.jdsports.ie", 200),
    ("https://duke.edu", 200),
    ("https://en.wikipedia.org", 200),
    ("https://www.prodirectsport.com", 200),
    ("https://www.nike.com", 200),   
    ("https://www.crocs.eu", 200)
]

# Thresholds for flakiness detection
FLAKY_THRESHOLD = 0.2  # Consider a test flaky if its failure rate is between 20% and 80%
MAX_FLAKY_THRESHOLD = 0.8

# Ensure CSV file is initialized with headers
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        f.write("timestamp,url,passed,status,attempt\n")

# Initialize flaky tests tracking file
if not os.path.exists(FLAKY_TESTS_FILE):
    with open(FLAKY_TESTS_FILE, "w") as f:
        f.write("url,total_runs,failures,flaky_rate,categorization\n")

@pytest.fixture(scope="session")
def browser():
    """Initialize and close a Playwright browser instance."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

# Track rerun attempts
test_attempts = defaultdict(int)

@pytest.mark.parametrize("url,expected_status", MOCK_DATA * 5)  # 10 test cases
def test_flaky_page(browser, url, expected_status):
    """
    Simulates a flaky test by introducing random failures.
    - 80% chance of passing
    - 20% chance of failing (randomly returns a 500 status)
    - Logs results to a CSV file
    """
    # Track attempt number for this test
    test_attempts[url] += 1
    attempt = test_attempts[url]
    
    page = browser.new_page()
    page.goto(url)
    time.sleep(random.uniform(0.1, 0.5))  # Simulate variable load time

    test_passed = random.random() < 0.8  # 80% chance of success
    status_code = expected_status if test_passed else 500  # 500 for simulated failures

    # Log test result (timestamp, URL, pass/fail, status, attempt number)
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.time()},{url},{int(test_passed)},{status_code},{attempt}\n")

    assert test_passed, f"Test failed for {url} with status {status_code}"

def analyze_flaky_tests():
    """
    Analyzes test results to identify flaky tests.
    - Flaky: tests that sometimes pass, sometimes fail (failure rate between thresholds)
    - Stable: tests that almost always pass (failure rate < FLAKY_THRESHOLD)
    - Problematic: tests that fail too often (failure rate > MAX_FLAKY_THRESHOLD)
    """
    try:
        df = pd.read_csv(LOG_FILE)
        
        if df.empty:
            raise ValueError("CSV file is empty. No data to analyze.")
            
        # Group by URL and calculate pass/fail stats
        url_stats = df.groupby("url").agg(
            total_runs=("passed", "count"),
            passes=("passed", "sum"),
        )
        
        url_stats["failures"] = url_stats["total_runs"] - url_stats["passes"]
        url_stats["failure_rate"] = url_stats["failures"] / url_stats["total_runs"]
        
        # Categorize tests based on failure rate
        def categorize(rate):
            if rate < FLAKY_THRESHOLD:
                return "stable"
            elif rate > MAX_FLAKY_THRESHOLD:
                return "problematic"
            else:
                return "flaky"
                
        url_stats["categorization"] = url_stats["failure_rate"].apply(categorize)
        
        # Save flaky tests report
        flaky_report = url_stats.reset_index()[["url", "total_runs", "failures", "failure_rate", "categorization"]]
        flaky_report.to_csv(FLAKY_TESTS_FILE, index=False)
        
        return url_stats
        
    except Exception as e:
        print(f"Error analyzing flaky tests: {e}")
        return None

def generate_reports():
    """
    Generates reports:
    1. Standard test report showing pass/fail counts
    2. Flakiness report showing test stability categories
    """
    try:
        # Read CSV with proper data type conversion
        df = pd.read_csv(LOG_FILE)

        if df.empty:
            raise ValueError("❌ CSV file is empty. No data to plot.")

        # Convert columns to correct types
        df["passed"] = df["passed"].astype(int)
        df["status"] = df["status"].astype(int)

        # Group by URL and count pass/fail occurrences
        pass_fail_counts = df.groupby("url")["passed"].value_counts().unstack(fill_value=0)

        # Plot test results as a stacked bar graph
        plt.figure(figsize=(12, 6))
        pass_fail_counts.plot(kind="bar", stacked=True, color=["red", "green"])
        plt.xlabel("Test URL")
        plt.ylabel("Test Count")
        plt.title("Flaky Test Results")
        plt.legend(["Failed", "Passed"])
        plt.tight_layout()
        plt.savefig(REPORT_FILE)
        plt.close()
        
        # Generate flaky tests report
        flaky_stats = analyze_flaky_tests()
        if flaky_stats is not None:
            category_counts = flaky_stats["categorization"].value_counts()
            
            plt.figure(figsize=(10, 6))
            category_counts.plot(kind="bar", color=["green", "orange", "red"])
            plt.xlabel("Test Category")
            plt.ylabel("Number of Tests")
            plt.title("Test Stability Analysis")
            plt.tight_layout()
            plt.savefig(FLAKY_REPORT_FILE)
            plt.close()
            
            print(f"✅ Reports generated: {REPORT_FILE} and {FLAKY_REPORT_FILE}")
            print("\nFlaky Tests Summary:")
            print(flaky_stats.groupby("categorization").size())
        
    except Exception as e:
        print(f"❌ Error generating reports: {e}")
        print("🔎 Debugging CSV contents:")
        try:
            print(pd.read_csv(LOG_FILE).head())
        except Exception as debug_e:
            print(f"⚠️ Failed to read CSV: {debug_e}")

if __name__ == "__main__":
    generate_reports()
