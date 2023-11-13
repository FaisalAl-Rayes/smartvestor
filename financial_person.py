class Person:
    def __init__(self, name: str, age: int) -> None:
        """Initialize a person object."""
        self.name = name
        self.age = age


class FinancialPerson(Person):
    def __init__(self,
                 name: str,
                 age: int,
                 gross_salary: float,
                 yearly_bonus: float = 0,
                 savings: float = 0) -> None:
        """Initialize a financial person object.

        :param name: Name of the financial person.
        :param age: Age of the financial person.
        :param gross_salary: Monthly gross salary.
        :param yearly_bonus: Yearly bonus percentage from the annual income in the format of 0.1 (10 %).
        """
        super().__init__(
            name=name, 
            age=age
        )
        self._gross_salary = gross_salary
        self._yearly_bonus = yearly_bonus
        self._savings = savings
        self.__income_tax = 0.15
        self.__social_security_contribution = 0.065
        self.__health_care_contribution = 0.045
        self.__tax_payer_monthly_discount = 2570
    
    @property
    def net_monthly_salary(self) -> float:
        income_tax: float = self._gross_salary * self.__income_tax
        social_security: float = self._gross_salary * self.__social_security_contribution
        health_care: float = self._gross_salary * self.__health_care_contribution

        deductions: float = income_tax + social_security + health_care

        return self._gross_salary - deductions + self.__tax_payer_monthly_discount

    @property
    def annual_bonus(self) -> float:
        return (12 * self._gross_salary) * self._yearly_bonus

    @property
    def net_annual_income(self) -> float:
        return (self.net_monthly_salary * 12) + self.annual_bonus

    @property
    def gross_salary(self) -> float:
        return self._gross_salary
    
    @property
    def net_monthly_income(self) -> float:
        return self.net_annual_income / 12

    @property
    def savings(self) -> float:
        return self._savings
