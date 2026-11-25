"""Helper functions for SQITK3073 Malaysian Tax Input Program (YA 2026)."""

from pathlib import Path
import math
import pandas as pd

# CSV files are stored in the same folder as this Python file.
BASE_FOLDER = Path(__file__).resolve().parent
USERS_FILE = BASE_FOLDER / "users.csv"
TAX_FILE = BASE_FOLDER / "tax_records.csv"

USER_COLUMNS = ["User ID", "IC Number"]
TAX_COLUMNS = [
    "User ID", "Test Case ID", "Year of Assessment", "Annual Income",
    "Total Tax Relief", "Chargeable Income", "Tax Before Rebate",
    "Tax Rebate", "Final Tax Payable"
]
MONEY_COLUMNS = [
    "Annual Income", "Total Tax Relief", "Chargeable Income",
    "Tax Before Rebate", "Tax Rebate", "Final Tax Payable"
]

# Upper limit of each chargeable-income band and its marginal tax rate.
TAX_BANDS = [
    (5000, 0.00),
    (20000, 0.01),
    (35000, 0.03),
    (50000, 0.06),
    (70000, 0.11),
    (100000, 0.19),
    (400000, 0.25),
    (600000, 0.26),
    (2000000, 0.28),
    (float("inf"), 0.30)
]

# Data given in the assignment (annual income, TOTAL relief).
TEST_CASES = [
    ("T01", 9000, 9000),
    ("T02", 40000, 9000),
    ("T03", 65000, 14000),
    ("T04", 120000, 18000),
    ("T05", 83000, 12000)
]


def initialize_csv_files():
    """Create CSV files with headers if they do not exist yet."""
    try:
        if not USERS_FILE.exists():
            pd.DataFrame(columns=USER_COLUMNS).to_csv(USERS_FILE, index=False)
        if not TAX_FILE.exists():
            pd.DataFrame(columns=TAX_COLUMNS).to_csv(TAX_FILE, index=False)
        return True
    except OSError as error:
        print(f"Error creating CSV files: {error}")
        return False


def load_csv(file_path, required_columns, dtype=None):
    """Read a CSV as a DataFrame; handle missing/invalid files safely."""
    if not file_path.exists():
        print(f"{file_path.name} is missing. Creating a new file...")
        try:
            pd.DataFrame(columns=required_columns).to_csv(file_path, index=False)
        except OSError as error:
            print(f"Could not create {file_path.name}: {error}")
            return None

    try:
        df = pd.read_csv(file_path, dtype=dtype, keep_default_na=False)
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing columns: {', '.join(missing_columns)}")
        return df[required_columns].copy()
    except (OSError, ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
        print(f"Error reading {file_path.name}: {error}")
        return None


def valid_ic(ic_number):
    """Check for an IC containing exactly 12 digits."""
    return len(ic_number) == 12 and ic_number.isdigit()


def register_user(user_id, ic_number):
    """Register a new user; prevent duplicate User IDs."""
    user_id = user_id.strip()
    ic_number = ic_number.strip()

    if not user_id:
        print("User ID cannot be empty.")
        return False
    if not valid_ic(ic_number):
        print("IC number must contain exactly 12 digits, without hyphens.")
        return False

    users_df = load_csv(USERS_FILE, USER_COLUMNS, dtype=str)
    if users_df is None:
        return False

    existing_ids = users_df["User ID"].astype(str).str.casefold()
    if user_id.casefold() in existing_ids.values:
        print("This User ID is already registered. Please log in.")
        return False

    # List -> dictionary -> DataFrame, before saving to CSV.
    user_list = [user_id, ic_number]
    user_dict = dict(zip(USER_COLUMNS, user_list))
    updated_df = (pd.DataFrame([user_dict], columns=USER_COLUMNS) if users_df.empty
                  else pd.concat([users_df, pd.DataFrame([user_dict])], ignore_index=True))

    try:
        updated_df.to_csv(USERS_FILE, index=False)
        print("Registration successful! Your password is the LAST 4 digits of your IC.")
        return True
    except OSError as error:
        print(f"Could not save registration: {error}")
        return False


def login_user(user_id, password):
    """Check the User ID and last four IC digits."""
    users_df = load_csv(USERS_FILE, USER_COLUMNS, dtype=str)
    if users_df is None:
        return False

    matched = users_df[
        users_df["User ID"].astype(str).str.casefold() == user_id.strip().casefold()
    ]
    if matched.empty:
        return False

    ic_number = str(matched.iloc[0]["IC Number"])
    return password == ic_number[-4:]


def input_nonnegative_amount(prompt):
    """Keep asking until a valid, non-negative RM amount is entered."""
    while True:
        try:
            value = float(input(prompt).strip().replace(",", ""))
            if not math.isfinite(value) or value < 0:
                print("Please enter a finite number that is 0 or higher.")
                continue
            return round(value, 2)
        except ValueError:
            print("Invalid input. Please enter a number, for example 40000.")
        except (EOFError, KeyboardInterrupt):
            print("\nInput cancelled.")
            return None


def calculate_tax(annual_income, total_relief):
    """Calculate resident individual income tax using the YA 2026 bands."""
    if (not math.isfinite(annual_income) or not math.isfinite(total_relief)
            or annual_income < 0 or total_relief < 0):
        raise ValueError("Income and relief must be finite, non-negative amounts.")

    chargeable_income = round(max(0.0, annual_income - total_relief), 2)

    # Marginal rates apply only to income WITHIN each band.
    tax_before_rebate = 0.0
    previous_limit = 0.0
    for upper_limit, rate in TAX_BANDS:
        taxable_in_band = max(0.0, min(chargeable_income, upper_limit) - previous_limit)
        tax_before_rebate += taxable_in_band * rate
        if chargeable_income <= upper_limit:
            break
        previous_limit = upper_limit
    tax_before_rebate = round(tax_before_rebate, 2)

    # RM400 rebate if chargeable income <= RM35,000.
    # A rebate cannot exceed tax due (unused rebate is not refundable).
    tax_rebate = min(400.0, tax_before_rebate) if chargeable_income <= 35000 else 0.0
    final_tax = round(max(0.0, tax_before_rebate - tax_rebate), 2)

    return chargeable_income, tax_before_rebate, round(tax_rebate, 2), final_tax


def create_tax_record(user_id, annual_income, total_relief, test_case_id=""):
    """Demonstrate list -> dictionary for one tax calculation."""
    chargeable, before_rebate, rebate, final = calculate_tax(annual_income, total_relief)
    values_list = [
        user_id, test_case_id, 2026, round(annual_income, 2),
        round(total_relief, 2), chargeable, before_rebate, rebate, final
    ]
    record_dict = dict(zip(TAX_COLUMNS, values_list))
    return values_list, record_dict


def print_tax_result(record):
    """Show a readable tax calculation result in RM."""
    print("\n========== TAX CALCULATION RESULT ==========")
    print(f"Year of Assessment  : {record['Year of Assessment']}")
    print(f"Annual Income       : RM {record['Annual Income']:,.2f}")
    print(f"Total Tax Relief    : RM {record['Total Tax Relief']:,.2f}")
    print(f"Chargeable Income   : RM {record['Chargeable Income']:,.2f}")
    print(f"Tax Before Rebate   : RM {record['Tax Before Rebate']:,.2f}")
    print(f"Tax Rebate          : RM {record['Tax Rebate']:,.2f}")
    print(f"FINAL TAX PAYABLE   : RM {record['Final Tax Payable']:,.2f}")
    print("============================================")


def show_data_processing(values_list, record_dict):
    """Display the list -> dictionary -> pandas DataFrame sequence."""
    print("\nSTEP 1 - Python LIST:")
    print(values_list)
    print("\nSTEP 2 - Python DICTIONARY:")
    print(record_dict)
    print("\nSTEP 3 - pandas DataFrame:")
    print(pd.DataFrame([record_dict]).to_string(index=False))


def save_tax_record(record_dict):
    """Append a new personal tax record without deleting earlier records."""
    existing = load_csv(TAX_FILE, TAX_COLUMNS,
                        dtype={"User ID": str, "Test Case ID": str})
    if existing is None:
        return False

    new_row = pd.DataFrame([record_dict], columns=TAX_COLUMNS)
    updated = new_row if existing.empty else pd.concat([existing, new_row], ignore_index=True)
    try:
        updated.to_csv(TAX_FILE, index=False)
        print("Tax record saved successfully to tax_records.csv!")
        return True
    except OSError as error:
        print(f"Could not save tax record: {error}")
        return False


def show_dataframe(df):
    """Display all money columns to two decimal places."""
    if df is None or df.empty:
        print("No matching records found.")
        return
    display = df.copy()
    for column in MONEY_COLUMNS:
        display[column] = pd.to_numeric(display[column], errors="coerce").map(
            lambda amount: f"{amount:,.2f}" if pd.notna(amount) else "N/A"
        )
    print(display.to_string(index=False))


def view_my_records(user_id):
    """Retrieve previously saved tax records of the logged-in user."""
    df = load_csv(TAX_FILE, TAX_COLUMNS,
                  dtype={"User ID": str, "Test Case ID": str})
    if df is None:
        return
    my_rows = df[(df["User ID"].str.casefold() == user_id.casefold()) &
                 (df["Test Case ID"] == "")]
    print("\n========== MY SAVED TAX RECORDS ==========")
    show_dataframe(my_rows)


def run_and_save_test_cases():
    """Compute T01-T05; replace earlier test rows without touching user records."""
    case_lists = []
    case_dicts = []
    for case_id, income, relief in TEST_CASES:
        values_list, record_dict = create_tax_record(
            "TEST_CASE", income, relief, test_case_id=case_id
        )
        case_lists.append(values_list)
        case_dicts.append(record_dict)

    # Show evidence of list -> dictionary -> DataFrame processing.
    print("\nEXAMPLE LIST (T01):")
    print(case_lists[0])
    print("\nEXAMPLE DICTIONARY (T01):")
    print(case_dicts[0])
    test_df = pd.DataFrame(case_dicts, columns=TAX_COLUMNS)
    print("\nFIVE TAX TEST CASES - pandas DataFrame:")
    show_dataframe(test_df)

    existing = load_csv(TAX_FILE, TAX_COLUMNS,
                        dtype={"User ID": str, "Test Case ID": str})
    if existing is None:
        return False

    case_ids = [case_id for case_id, _, _ in TEST_CASES]
    is_old_test = ((existing["User ID"] == "TEST_CASE") &
                   (existing["Test Case ID"].isin(case_ids)))
    remaining = existing.loc[~is_old_test]
    updated = test_df if remaining.empty else pd.concat([remaining, test_df], ignore_index=True)

    try:
        updated.to_csv(TAX_FILE, index=False)
        print("\nAll five test cases saved to tax_records.csv!")
        return True
    except OSError as error:
        print(f"Could not save test cases: {error}")
        return False


def view_test_cases():
    """Retrieve the five test cases from the saved CSV using pandas."""
    df = load_csv(TAX_FILE, TAX_COLUMNS,
                  dtype={"User ID": str, "Test Case ID": str})
    if df is None:
        return
    case_ids = [case_id for case_id, _, _ in TEST_CASES]
    tests = df[(df["User ID"] == "TEST_CASE") &
               (df["Test Case ID"].isin(case_ids))]
    print("\n========== SAVED TAX TEST CASES ==========")
    show_dataframe(tests)
