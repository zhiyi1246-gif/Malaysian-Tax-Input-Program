"""Main menu for SQITK3073 Malaysian Tax Input Program (YA 2026)."""

from functions import (
    initialize_csv_files,
    register_user,
    login_user,
    input_nonnegative_amount,
    create_tax_record,
    print_tax_result,
    show_data_processing,
    save_tax_record,
    view_my_records,
    run_and_save_test_cases,
    view_test_cases
)


def logged_in_menu(user_id):
    """Only authenticated users can calculate or retrieve tax records."""
    while True:
        print(f"\n========== WELCOME, {user_id} ==========")
        print("1. Calculate and save my tax")
        print("2. View my saved tax records")
        print("3. Run and save the FIVE test cases (T01-T05)")
        print("4. View saved test cases")
        print("5. Logout")
        choice = input("Choose an option (1-5): ").strip()

        if choice == "1":
            print("\nPlease enter your annual income and TOTAL eligible tax relief.")
            print("Include the RM9,000 individual relief if you are eligible.")
            annual_income = input_nonnegative_amount("Annual Income (RM): ")
            if annual_income is None:
                continue
            total_relief = input_nonnegative_amount("Total Tax Relief (RM): ")
            if total_relief is None:
                continue

            # Python LIST -> DICTIONARY -> pandas DataFrame -> CSV.
            values_list, record_dict = create_tax_record(
                user_id, annual_income, total_relief
            )
            print_tax_result(record_dict)
            show_data_processing(values_list, record_dict)
            save_tax_record(record_dict)

        elif choice == "2":
            view_my_records(user_id)
        elif choice == "3":
            run_and_save_test_cases()
        elif choice == "4":
            view_test_cases()
        elif choice == "5":
            print("You have logged out.")
            break
        else:
            print("Invalid option. Please enter 1, 2, 3, 4 or 5.")


def main():
    """Show the registration/login menu until the user exits."""
    if not initialize_csv_files():
        return

    print("============================================")
    print("   MALAYSIAN TAX INPUT PROGRAM - YA 2026")
    print("============================================")

    while True:
        print("\n========== MAIN MENU ==========")
        print("1. Register new user")
        print("2. Login")
        print("3. Exit")
        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            user_id = input("Create User ID: ").strip()
            ic_number = input("Enter 12-digit IC (without '-'): ").strip()
            register_user(user_id, ic_number)

        elif choice == "2":
            user_id = input("Enter User ID: ").strip()
            password = input("Password (last 4 digits of your IC): ").strip()
            if login_user(user_id, password):
                print("Login successful!")
                logged_in_menu(user_id)
            else:
                print("Login failed! Please check your User ID and password.")

        elif choice == "3":
            print("Thank you for using the Malaysian Tax Input Program!")
            break
        else:
            print("Invalid option. Please enter 1, 2 or 3.")


if __name__ == "__main__":
    main()
