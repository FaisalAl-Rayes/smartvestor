import json

import numpy as np

from financial_person import FinancialPerson
import mortgage_calculator
import finance_enums


class Smartvestor:
    """A thing that will tell you how to better manage your money."""

    def __init__(self, financial_person: FinancialPerson) -> None:
        """Initializes Smartvestor.

        :param financial_person: the financial person of concern.
        """
        self._financial_person = financial_person

        # This is a simplification of the budget
        # if you have a higher income then less will go into groceries and if your smart then more goes into your savings and investments.
        # however housing costs should be max 0.3 (30%) always, regardless of your net monthly income.
        self.__budgeting: dict[str, float] = {
            finance_enums.BudgetCategories.HOUSING.value: 0.3,
            finance_enums.BudgetCategories.GROCERIES.value: 0.2 if self._financial_person.gross_salary <= 110_000 else 0.15,
            finance_enums.BudgetCategories.SAVINGS_AND_INVESTMENTS.value: 0.3 if self._financial_person.gross_salary <= 110_000 else 0.35,
            finance_enums.BudgetCategories.LEISUER.value: 0.2,
        }

        # Preprocessing
        self._monthly_budget: dict[str, float] = self.define_budget()
        self._emergency_fund: float = np.multiply(
            3,
            np.add(self._monthly_budget[finance_enums.BudgetCategories.HOUSING.value], self._monthly_budget[finance_enums.BudgetCategories.GROCERIES.value])
        )

    def define_budget(self) -> dict[str, float]:
        """Distributes the monthly income in a way to not live more than you can afford.

        :return: the budget dictionary
        """
        salary_slice = lambda category: round(np.multiply(self.__budgeting[category], self._financial_person.net_monthly_income))
        budget: dict[str, float] = {
            finance_enums.BudgetCategories.HOUSING.value: salary_slice(category=finance_enums.BudgetCategories.HOUSING.value),
            finance_enums.BudgetCategories.GROCERIES.value: salary_slice(category=finance_enums.BudgetCategories.GROCERIES.value),
            finance_enums.BudgetCategories.SAVINGS_AND_INVESTMENTS.value: salary_slice(category=finance_enums.BudgetCategories.SAVINGS_AND_INVESTMENTS.value),
            finance_enums.BudgetCategories.LEISUER.value: salary_slice(category=finance_enums.BudgetCategories.LEISUER.value),
        }
        assert sum(budget.values()) == round(self._financial_person.net_monthly_income), (
            "Budgeting values don't add up to the net monthly income.\n"
            + f"Budgeting values detected {self.__budgeting.values()} make sure they add up to 1."
        )
        return budget

    def is_financially_stable(self) -> bool:
        """Decides if the current financial situation allows for starting to save for a house.

        :return: True if you are in a position to start your saving journy to buy a house, False if otherwise
        """
        # Emergency fund in place before anything else.
        if self._financial_person.savings < self._emergency_fund:
            print("Not financially stable: You first need to save at least 3 months worth of necessary expenses "
                  f"which according to your salary should be {self._emergency_fund:,.1f} CZK.")
            return False
        # Save and Invest your money to prepare for a mortgage or a long term plan for buying a home cash.
        else:
            savings_allocated_money: float = self._monthly_budget[finance_enums.BudgetCategories.SAVINGS_AND_INVESTMENTS.value]
            print(f"Financially stable: You have {savings_allocated_money:,.1f} CZK/month to "
                  "divide between saving and investing to prepare for your home purchase.")
            return True

    def mortgage_preparation(self, property_price: float, down_payment_percentage: float) -> int:
        """Calculates how many months to have the down payment in case

        :param property_price: The price of the property.
        :param down_payment_percentage: The down payment percentage for the property (minimum 10% in Czechia 2023)
        """
        down_payment: float = np.multiply(property_price, down_payment_percentage)
        amount_saved: float = np.subtract(self._financial_person.savings, self._emergency_fund)
        monthly_saving: float = np.multiply(
            self.__budgeting[finance_enums.BudgetCategories.SAVINGS_AND_INVESTMENTS.value],
            self._financial_person.net_monthly_income
        )
        months_to_save: int = 0

        while (amount_saved < down_payment):
            amount_saved += monthly_saving
            months_to_save += 1
        
        return months_to_save / 12

    def cash_house(self, current_rent: float, property_price: float) -> float:
        """Calculates how many months to have the property price.

        :param current_rent: The price of the monthly rent.
        :param property_price: The price of the property.
        """
        amount_saved: float = np.subtract(self._financial_person.savings, self._emergency_fund)

        monthly_post_housing: float = np.subtract(
            np.multiply(
                self.__budgeting[finance_enums.BudgetCategories.HOUSING.value],
                self._financial_person.net_monthly_income
            ),
            current_rent
        )

        # Adjusting the monthly savings in accordance to the housing budget leftover (monthly_post_housing)
        monthly_saving: float = np.multiply(
                self.__budgeting[finance_enums.BudgetCategories.SAVINGS_AND_INVESTMENTS.value],
                self._financial_person.net_monthly_income
            )
        if monthly_post_housing > 0:
            monthly_saving += monthly_post_housing
        months_to_save: int = 0

        while (amount_saved < property_price):
            amount_saved += monthly_saving
            months_to_save += 1
        
        return months_to_save / 12

    def house_timeline(self,
                       current_rent: float,
                       property_price: float,
                       strategy: finance_enums.HouseStrategies) -> None:
        """Illustrates the timeline of the house aquisition.

        :param current_rent: The price of the monthly rent.
        :param property_price: The price of the property.
        :param strategy: The strategy to buying the house (mortgage or cash)
        """
        years_to_save: float = 0.0
        total_cost: float = 0.0
        if strategy == finance_enums.HouseStrategies.MORTGAGE:
            years_to_save = round(
                self.mortgage_preparation(
                    property_price= property_price,
                    down_payment_percentage=0.2
                )
            )
            mortgage_calc = mortgage_calculator.MortgageCalculator()
            mortgage_df, _ = mortgage_calc.mortgage_breakdown(
                property_price,
                down_payment_percentage=0.2,
                max_interest_rate=mortgage_calculator.MAXIMUM_INTEREST_RATE,
                loan_term=15,
                with_insurance=False
            )
            total_cost = round(
                np.add(
                    mortgage_calc.get_total_cost(mortgage_breakdown_df=mortgage_df),
                    np.multiply(
                        np.multiply(current_rent, 12),
                        years_to_save 
                    )
                )
            )
        elif strategy == finance_enums.HouseStrategies.CASH:
            years_to_save = round(
                self.cash_house(
                    current_rent=current_rent,
                    property_price=property_price
                )
            )
            total_cost = round(
                np.add(
                    property_price,
                    np.multiply(
                        np.multiply(current_rent, 12),
                        years_to_save 
                    )
                )
            )
        else:
            raise ValueError(f"The selected strategy ({strategy}) is not supported.\n"
                             f"Select a supported strategy: {[s.value for s in finance_enums.HouseStrategies]}")

        print(f"It would take approx. {years_to_save:,.0f} years to save and a total cost of approx. {total_cost:,.0f} " 
              f"CZK To get your own house using the {strategy.value} strategy")
        return





if __name__ == "__main__":
    # Prompted input.
    # Financial Person.
    name: str = input("Name: ")
    age: int = int(input("Age: "))
    gross_salary: float = float(input("Gross salary (Annual): "))
    bonuses: float = float(input("Annual bonus (0.1 == 10%): "))
    savings: float = float(input("Savings: "))

    # House related.
    rent: float = float(input("Monthly rent: "))
    property_price: float(input("Property price: "))

    fp: FinancialPerson = FinancialPerson(name, age, gross_salary, bonuses, savings)
    smartvestor = Smartvestor(financial_person=fp)
    print(json.dumps(smartvestor.define_budget(), indent=4))
    print("--------------------------------------------------------------------------------")
    smartvestor.is_financially_stable()
    print("--------------------------------------------------------------------------------")
    smartvestor.house_timeline(rent, property_price, finance_enums.HouseStrategies.CASH)
    print("--------------------------------------------------------------------------------")
    smartvestor.house_timeline(rent, property_price, finance_enums.HouseStrategies.MORTGAGE)
