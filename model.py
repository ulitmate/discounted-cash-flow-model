from discounted_cash_flow_model.discounted_cash_flow_model import DiscountedCashFlowModel
from financial_modeling_prep.financial_modeling_prep import FinancialModelingPrep
import argparse
import logging
import sys

class IntegerAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values < 1:
            parser.error(f"{option_string} must be greater than or equal to 1.")
        
        setattr(namespace, self.dest, values)

class FloatAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values < 0:
            parser.error(f"{option_string} must be greater than 0.")
        
        setattr(namespace, self.dest, values)

class RiskAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values not in ["conservative", "moderate", "bullish"]:
            parser.error(f"{option_string} must be 1 of the 3 following options...\n1. conservative\n2. moderate\n3. bullish")

        setattr(namespace, self.dest, values)

def _configure_logger(debug):
    logger = logging.getLogger("LOGGER")

    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    return logger

def _str_to_bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use the DCF model to calculate fair value for various companies.')
    parser.add_argument('--ticks', nargs='+', help='Specify ticker symbols (1 or more).', required=True)
    parser.add_argument('--minimum_years', action=IntegerAction, help='Specify the minimum amount of years of data points needed to perform the DCF calculation.', type=int, default=4)
    parser.add_argument('--maximum_years', action=IntegerAction, help='Specify the maximum amount of years of data points needed to perform the DCF calculation.', type=int, default=10)
    parser.add_argument('--years_to_project', action=IntegerAction, help='Specify the number of years to project future earnings.', type=int, default=4)
    parser.add_argument('--return_percentage', action=FloatAction, help='Specify the required rate of return in terms of a percentage.', type=float, default=8.0)
    parser.add_argument('--perpetual_growth_rate', action=FloatAction, help='Perpetual growth rate is the rate at which the free cash flow will grow forever. This number will drastically change the fair value, thus the default is the growth rate of GDP.', type=float, default=2.5)
    parser.add_argument('--margin_of_safety', action=FloatAction, help='Specify the margin of safety in terms of a percentage to be applied after the fair value is calculated.', type=float, default=50.0)
    parser.add_argument('--risk', action=RiskAction, help='Specify the level of risk you would like to take. Choose between `conservative`, `moderate`, or `bullish`.', default='conservative')
    parser.add_argument('--debug', help="Enable debug option.", type=_str_to_bool, default=False)
    args = parser.parse_args()

    print("--------- INPUT ARGUMENTS ---------")
    print(f"Ticker symbols -> {args.ticks}")
    print(f"Minimum amount of years of data -> {args.minimum_years} {'year' if args.minimum_years == 1 else 'years'}")
    print(f"Maximum amount of years of data -> {args.maximum_years} {'year' if args.maximum_years == 1 else 'years'}")
    print(f"Number of years to project future earnings -> {args.years_to_project} {'year' if args.years_to_project == 1 else 'years'}")
    print(f"Required rate of return -> {args.return_percentage} %")
    print(f"Perpetual growth rate -> {args.perpetual_growth_rate} %")
    print(f"Margin of safety -> {args.margin_of_safety} %")
    print(f"Risk -> {args.risk}")
    print(f"Debug -> {args.debug}\n")
    
    logger = _configure_logger(args.debug)

    api = FinancialModelingPrep(logger)
    model = DiscountedCashFlowModel(
        args.return_percentage,  
        args.years_to_project, 
        args.risk, 
        args.perpetual_growth_rate, 
        args.margin_of_safety,
        logger
    )

    for tick in args.ticks:
        print(f"Analyzing ticker symbol {tick}...")

        try:
            print("Fetching financial statements...")
            financials = api.get_financials(tick, args.minimum_years, args.maximum_years)

            print("Fetching quote data...")
            quotes = api.get_quotes(tick)
        except Exception as e:
            print(f"Failed to fetch data from api -> {e}")
            sys.exit()

        try:
            print("Calculating DCF...")
            fair_value, fair_value_with_margin_of_safety = model.calculate(tick, financials, quotes)
            print(f"Fair value -> ${round(fair_value, 2)}\nFair value w/ margin of safety -> ${round(fair_value_with_margin_of_safety, 2)}\n")
        except Exception as e:
            print(f"Failed to use DCF model -> {e}")
