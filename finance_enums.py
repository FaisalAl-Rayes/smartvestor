import enum

class BudgetCategories(enum.Enum):
    HOUSING = "housing"
    GROCERIES = "groceries"
    SAVINGS_AND_INVESTMENTS = "savings_and_investments"
    LEISUER = "leisure"

class HouseStrategies(enum.Enum):
    MORTGAGE = "mortgage"
    CASH = "cash"