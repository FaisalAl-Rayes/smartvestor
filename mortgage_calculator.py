import base64
import pathlib
import typing
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from matplotlib.ticker import FuncFormatter

from financial_person import FinancialPerson

CURRENT_INTEREST_RATE: int = 6     # (currently ranging from 5.8% to 7% in Czechia 2023)


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

        self.mortgage_summary: str = ""

    def analyze(self, financial_person: FinancialPerson) -> None:
        """Analyzes the maximum amount of mortgage you can afford.

        :param financial_person: the financial person of concern
        """
        pass

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

    def mortgage_breakdown(
            self,
            property_price: float,
            down_payment_percentage: float,
            interest_rate: float,
            loan_term: float,
            with_insurance: bool = False,
            monthly_extra_payment: float = 0.0
    ) -> pd.DataFrame:
        """Breaks down the mortgage to provide a detailed overview for a given financial person.

        :param property_price: The price of the property.
        :param down_payment_percentage: The down payment percentage for the property (minimum 10% in Czechia 2023)
        :param interest_rate: The maximum annual interest rate
        :param loan_term: The loan term (typically 15 or 30 years)
        :param with_insurance: The option to add insurance for the mortgage in the case of unforeseeable tragedies (illness, death)
        :param monthly_extra_payment: The monthly extra payment paid to the principal of the mortgage loan.
        """
        down_payment_percentage: float = down_payment_percentage if down_payment_percentage > 1 else np.multiply(down_payment_percentage, 100)
        down_payment: float = np.multiply(property_price, np.divide(down_payment_percentage, 100))

        # For reports
        msg: str = f"{property_price = :,.0f} CZK\n{down_payment = :,.0f} CZK\n{interest_rate = } %\n{loan_term = } years\n{with_insurance = }\n{monthly_extra_payment = :,.0f} CZK\n\n"

        principal: float = property_price - down_payment
        total_payments: int = int(loan_term * 12)
        monthly_interest_rate = (interest_rate / 12) / 100

        # Create empty lists to store the details
        month_number = [0]
        monthly_payment = [0]
        principal_balance = [principal]
        principal_payment = [0]
        interest_payment = [0]
        insurance_payment = [0]

        # Calculate the monthly payment.
        numerator: float = np.multiply(principal, np.multiply(monthly_interest_rate, np.power(1 + monthly_interest_rate, total_payments)))
        denominator: float = np.power(1 + monthly_interest_rate, total_payments) - 1
        monthly_payment_value: float = np.multiply(numerator / denominator, 1.088) if with_insurance else numerator / denominator
        insurance_payment_value: float = np.multiply(numerator / denominator, 0.088) if with_insurance else 0

        months_to_payoff: int = 0
        remaining_balance = principal
        for month in range(1, total_payments + 1):
            months_to_payoff = month
            if remaining_balance - monthly_extra_payment < 0:
                remaining_balance += monthly_extra_payment
                print(f"The last extra payment needed is less ({remaining_balance:,.0f} CZK.)")
                break

            # Calculate the interest payment for the current month
            interest_payment_value = np.multiply(remaining_balance, monthly_interest_rate)

            # Calculate the principal payment for the current month
            principal_payment_value = monthly_payment_value - insurance_payment_value - interest_payment_value
            # The monthly extra payment to the principal.
            if monthly_extra_payment:
                principal_payment_value += monthly_extra_payment

            # Update the remaining balance
            remaining_balance -= principal_payment_value

            # Append the values to the lists
            month_number.append(month)
            monthly_payment.append(monthly_payment_value + monthly_extra_payment)
            principal_balance.append(remaining_balance)
            principal_payment.append(principal_payment_value)
            interest_payment.append(interest_payment_value)
            insurance_payment.append(insurance_payment_value)

        msg += f"The monthly mortgage payment would be {monthly_payment_value:,.0f} CZK/month.\n"
        if monthly_extra_payment:
            msg += f"Plus {monthly_extra_payment:,.0f} monthly paid to the principal resulting in a total monthly payment of {monthly_payment_value + monthly_extra_payment:,.0f} CZK\n"
        msg += f"It would take {months_to_payoff / 12:.2f} myears to payoff the mortgage.\n"
        print(msg)
        self.mortgage_summary = msg.replace("\n", "<br>")

        # Create the DataFrame
        data: dict[str, list[typing.Any]] = {
            "Month": month_number,
            "Monthly Payment": monthly_payment,
            "Principal Balance": principal_balance,
            "Principal Payment": principal_payment,
            "Interest Payment": interest_payment,
            "Insurance Payment": insurance_payment
        }
        df = pd.DataFrame(data)


        return df

    @staticmethod
    def mortgage_breakdown_plot(
            mortgage_breakdown_df: pd.DataFrame,
    ) -> plt.plot:
        """Plots a graph with a detailed overview of the mortgage.

        :param mortgage_breakdown_df: the breakdown of all monthly payments and their distribution.
        :return: None
        """
        # Extract the Month and Principal Payment columns
        months = mortgage_breakdown_df["Month"]
        principal_balance = mortgage_breakdown_df["Principal Balance"]
        interest_paid = mortgage_breakdown_df["Interest Payment"].cumsum()
        insurance_paid = mortgage_breakdown_df["Insurance Payment"].cumsum()
        principal_paid = mortgage_breakdown_df["Principal Payment"].cumsum()

        # Calculate total cost (Principal Paid + Interest Paid + Insurance Paid)
        total_cost = principal_paid + interest_paid + insurance_paid

        # Create a plot
        plt.figure(figsize=(10, 8))
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
            xytext=(months.iloc[-1] - 5, final_total_cost + np.multiply(final_total_cost, 0.1)),
            bbox=dict(boxstyle="round", facecolor="lightgray", edgecolor="gray", alpha=0.7),
            arrowprops=dict(facecolor="black", arrowstyle="wedge,tail_width=0.7", alpha=0.7)
        )
        plt.annotate(
            f'{final_total_interest_paid:,.0f} CZK',
            xy=(months.iloc[-1], final_total_interest_paid),
            xytext=(months.iloc[-1] + 2, final_total_interest_paid + np.multiply(final_total_interest_paid, 0.2)),
            bbox=dict(boxstyle="round", facecolor="lightgray", edgecolor="gray", alpha=0.7),
            arrowprops=dict(facecolor="black", arrowstyle="wedge,tail_width=0.7", alpha=0.7)
        )
        plt.annotate(
            f'{final_total_insurance_paid:,.0f} CZK',
            xy=(months.iloc[-1], final_total_insurance_paid),
            xytext=(months.iloc[-1] + 3, final_total_insurance_paid + 200000),
            bbox=dict(boxstyle="round", facecolor="lightgray", edgecolor="gray", alpha=0.7),
            arrowprops=dict(facecolor="black", arrowstyle="wedge,tail_width=0.7", alpha=0.7)
        )

        # Show the plot
        plt.grid(True)
        return plt

    @staticmethod
    def _encode_plot(plot_to_encode: plt.plot) -> bytes:
        tmp_file = BytesIO()
        plot_to_encode.savefig(tmp_file, format='png')
        return base64.b64encode(tmp_file.getvalue())

    def create_html_report(self, plot_for_report: plt.plot, mortgage_breakdown: pd.DataFrame, file_name: str) -> None:

        # Format the prices to be more readable
        def format_with_commas(value):
            return f'{value:,.0f}'
        formatted_mb = mortgage_breakdown.map(format_with_commas)

        decoded_plot: str = self._encode_plot(plot_for_report).decode('utf-8')
        env = Environment(loader=FileSystemLoader(pathlib.Path(__file__).parent / "templates/"))
        template = env.get_template("report.html")

        data = {
            "file_name": file_name.title().replace('_', ' '),
            "decoded_plot": decoded_plot,
            "mortgage_summary": self.mortgage_summary,
            "brs": '<br>'.join([' ' for _ in range(1, 12)]),
            "mortgage_breakdown": formatted_mb.to_html()
        }

        report_html = template.render(data)

        with open(f"{file_name}.html", "w") as f:
            f.write(report_html)

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
    mortgage_calculator = MortgageCalculator()

    mb_df = mortgage_calculator.mortgage_breakdown(
        property_price=1234567,
        down_payment_percentage=20,
        interest_rate=CURRENT_INTEREST_RATE,
        loan_term=30,
        with_insurance=True,
        monthly_extra_payment=12345
    )
    plot: plt.plot = mortgage_calculator.mortgage_breakdown_plot(mortgage_breakdown_df=mb_df)

    mortgage_calculator.create_html_report(plot_for_report=plot, mortgage_breakdown=mb_df, file_name="YOUR-DESIRED-FILE-NAME")
