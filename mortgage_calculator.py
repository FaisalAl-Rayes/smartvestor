import typing

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

from financial_person import FinancialPerson

MAXIMUM_INTEREST_RATE: int = 6     # (currently ranging from 5.8% to 7% in Czechia 2023)

class MortgageCalculator:
    """Calculates mortgage breakdown of financial persons."""

    def __init__(self) -> None:
        # DTI is the total debt allowed on your name (calculated as DTI * annual net income).
        # LTV is the maximum amount you can borrow from the bank ( calculated as LTV * price of the property).
        self.__borrowing_limits: dict[str, dict] = {
            "up_to_35": {
                "max_dti": 9.5,
                "max_ltv": 0.9
            },
            "36_and_above": {
                "max_dti": 8.5,
                "max_ltv": 0.8
            }
        }

    def analyze(self, financial_person: FinancialPerson) -> None:
        """Analyzes the maximum amount of mortgage you can afford.

        :param financial_person: the financial person of concern
        :return: None
        """
        net_annual_income: float = financial_person.net_annual_income
        return

    def max_debt_to_income(self, financial_person: FinancialPerson):
        """Calculates the maximum amount of debt you can have on your name.

        :param financial_person: the financial person of concern.
        :return: the max amount debt you can have on your name.
        """
        if financial_person.age < 35:
            return np.multiply(financial_person.net_annual_income, self.__borrowing_limits["up_to_35"]["max_dti"])
        return np.multiply(financial_person.net_annual_income, self.__borrowing_limits["36_and_above"]["max_dti"])

    def max_loan_to_value(self, financial_person: FinancialPerson, property_price: float):
        """Calculates the maximum amount of money you can borrow from a bank for a mortgage.

        :param financial_person: the financial person of concern.
        :param property_price: the full price of the property.
        :return: the max amount possible to borrow from the bank.
        """
        if financial_person.age < 35:
            return np.multiply(property_price, self.__borrowing_limits["up_to_35"]["max_ltv"])
        return np.multiply(property_price, self.__borrowing_limits["36_and_above"]["max_ltv"])

    @staticmethod
    def mortgage_breakdown(
            property_price: float,
            down_payment_percentage: float,
            max_interest_rate: float,
            loan_term: float,
            with_insurance: bool = False
    ) -> tuple[pd.DataFrame, float]:
        """Breaks down the mortgage to provide a detailed overview for a given financial person.

        :param property_price: The price of the property.
        :param down_payment_percentage: The down payment percentage for the property (minimum 10% in Czechia 2023)
        :param max_interest_rate: The maximum annual interest rate
        :param loan_term: The loan term (typically 15 or 30 years)
        :param with_insurance: The option to add insurance for the mortgage in the case of unforeseeable tragedies (illness, death)
        :return: None
        """
        down_payment_percentage: float = down_payment_percentage if down_payment_percentage > 1 else np.multiply(down_payment_percentage, 100)
        down_payment: float = np.multiply(property_price, np.divide(down_payment_percentage, 100))
        if 20 <= down_payment_percentage < 30:
            interest_rate: float = np.multiply(max_interest_rate, 0.95305164)
        elif down_payment_percentage >= 30:
            interest_rate: float = np.multiply(max_interest_rate, 0.92957746)
        else:
            interest_rate: float = max_interest_rate

        principal: float = property_price - down_payment
        total_payments: int = int(loan_term * 12)
        monthly_interest_rate = (interest_rate / 12) / 100

        # Create empty lists to store the details
        month_number = []
        monthly_payment = []
        principal_payment = []
        interest_payment = []
        insurance_payment = []

        # Calculate the monthly payment.
        numerator: float = np.multiply(principal, np.multiply(monthly_interest_rate, np.power(1 + monthly_interest_rate, total_payments)))
        denominator: float = np.power(1 + monthly_interest_rate, total_payments) - 1
        monthly_payment_value: float = np.multiply(numerator / denominator, 1.088) if with_insurance else numerator / denominator
        insurance_payment_value: float = np.multiply(numerator / denominator, 0.088) if with_insurance else 0

        remaining_balance = principal
        for month in range(1, total_payments + 1):
            # Calculate the interest payment for the current month
            interest_payment_value = np.multiply(remaining_balance, monthly_interest_rate)

            # Calculate the principal payment for the current month
            principal_payment_value = monthly_payment_value - insurance_payment_value - interest_payment_value

            # Update the remaining balance
            remaining_balance -= principal_payment_value

            # Append the values to the lists
            month_number.append(month)
            monthly_payment.append(monthly_payment_value)
            principal_payment.append(principal_payment_value)
            interest_payment.append(interest_payment_value)
            insurance_payment.append(insurance_payment_value)

        # Create the DataFrame
        data: dict[str, list[typing.Any]] = {
            "Month": month_number,
            "Monthly Payment": monthly_payment,
            "Principal Payment": principal_payment,
            "Interest Payment": interest_payment,
            "Insurance Payment": insurance_payment
        }
        return pd.DataFrame(data), principal

    @staticmethod
    def plot_mortgage_breakdown(
            mortgage_breakdown_df: pd.DataFrame,
            principal: float
    ) -> None:
        """Plots a graph with a detailed overview of the mortgage.

        :param mortgage_breakdown_df: the breakdown of all monthly payments and their distribution.
        :param principal: the principal of the mortgage loan.
        :return: None
        """
        # Extract the Month and Principal Payment columns
        months = mortgage_breakdown_df["Month"]
        principal_balance = principal - mortgage_breakdown_df["Principal Payment"].cumsum()
        interest_paid = mortgage_breakdown_df["Interest Payment"].cumsum()
        insurance_paid = mortgage_breakdown_df["Insurance Payment"].cumsum()
        principal_paid = mortgage_breakdown_df["Principal Payment"].cumsum()

        # Calculate total cost (Principal Paid + Interest Paid + Insurance Paid)
        total_cost = principal_paid + interest_paid + insurance_paid

        # Create a plot
        plt.figure(figsize=(10, 6))
        plt.plot(months, principal_balance, label="Principal Balance", marker="o", linestyle="-", linewidth=1)
        plt.plot(months, interest_paid, label="Total Interest Paid", marker="x", linestyle="-", linewidth=1)
        plt.plot(months, insurance_paid, label="Total Insurance Paid", marker="s", linestyle="-", linewidth=1)
        plt.plot(months, principal_paid, label="Principal Paid", marker="^", linestyle="-", linewidth=1)
        plt.plot(months, total_cost, label="Total Cost", marker="D", linestyle="-", linewidth=1)

        # Set labels and title
        plt.title("Mortgage Payment Breakdown")
        plt.xlabel("Month")
        plt.ylabel("Amount (CZK)")

        # Define a function to format y-axis ticks as thousands with comma separators
        def thousands_formatter(x, pos):
            return f"{x:,.0f}"

        # Apply the custom formatter to the y-axis
        plt.gca().yaxis.set_major_formatter(FuncFormatter(thousands_formatter))

        # Add a legend
        plt.legend()

        # Add an annotation for the final value of Total Cost, Total Interest Paid, and Total Insurance Paid
        # Get the final values from the DataFrame
        final_total_cost = total_cost.iloc[-1]
        final_total_interest_paid = interest_paid.iloc[-1]
        final_total_insurance_paid = insurance_paid.iloc[-1]
        plt.annotate(
            f'{final_total_cost:,.0f} CZK',
            xy=(months.iloc[-1], final_total_cost),
            xytext=(months.iloc[-1] + 5, final_total_cost + np.multiply(final_total_cost, 0.02))
        )
        plt.annotate(
            f'{final_total_interest_paid:,.0f} CZK',
            xy=(months.iloc[-1], final_total_interest_paid),
            xytext=(months.iloc[-1] + 5, final_total_interest_paid + np.multiply(final_total_interest_paid, 0.02))
        )
        plt.annotate(
            f'{final_total_insurance_paid:,.0f} CZK',
            xy=(months.iloc[-1], final_total_insurance_paid),
            xytext=(months.iloc[-1] + 5, final_total_insurance_paid + np.multiply(final_total_insurance_paid, 0.02))
        )

        # Show the plot
        plt.grid(True)
        plt.show()

    @staticmethod
    def get_total_cost(mortgage_breakdown_df: pd.DataFrame) -> float:
        """Calculates the total cost of the mortgage over the lifetime of it.

        :param mortgage_breakdown_df: the breakdown of all monthly payments and their distribution.
        :return: the total cose of the mortgage.
        """
        interest_paid = mortgage_breakdown_df["Interest Payment"].cumsum()
        insurance_paid = mortgage_breakdown_df["Insurance Payment"].cumsum()
        principal_paid = mortgage_breakdown_df["Principal Payment"].cumsum()

        # Calculate total cost (Principal Paid + Interest Paid + Insurance Paid)
        total_cost = principal_paid + interest_paid + insurance_paid

        return total_cost.iloc[-1]

if __name__ == "__main__":
    # Prompted input.
    name: str = input("Name: ")
    age: int = int(input("Age: "))
    gross_salary: float = float(input("Gross salary (Annual): "))
    bonuses: float = float(input("Annual bonus (0.1 == 10%): "))
    savings: float = float(input("Savings: "))

    # House related.
    property_price: float(input("Property price: "))

    fp: FinancialPerson = FinancialPerson(name, age, gross_salary, bonuses, savings)

    mortgage_calculator = MortgageCalculator()
    mb_df, m_principal = mortgage_calculator.mortgage_breakdown(
        property_price=property_price,
        down_payment_percentage=20,
        max_interest_rate=5.19,
        loan_term=15,
        with_insurance=False
    )
    mortgage_calculator.plot_mortgage_breakdown(mortgage_breakdown_df=mb_df, principal=m_principal)
