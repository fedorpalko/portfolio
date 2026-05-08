from kelly import kelly_bet_sizing_simple


def main():
    bankroll = 100
    prob1 = 0.5
    probx = 0.25
    prob2 = 0.25
    odds1 = 2.50
    oddsx = 2.22
    odds2 = 2.14

    print(
        "BetBot says: Bet on:",
        kelly_bet_sizing_simple(bankroll, prob1, probx, prob2, odds1, oddsx, odds2),
    )


if __name__ == "__main__":
    main()
