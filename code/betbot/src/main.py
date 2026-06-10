from kelly import kelly_full_analysis


def main():
    bankroll = 100
    prob1 = 0.5
    probx = 0.25
    prob2 = 0.25
    odds1 = 2.50
    oddsx = 2.22
    odds2 = 2.14
    fraction = 0.25

    results = kelly_full_analysis(bankroll, prob1, probx, prob2, odds1, oddsx, odds2, fraction=fraction)

    print(f"BetBot Analysis  |  bankroll: ${bankroll:.2f}  |  kelly fraction: {fraction:.0%}\n")
    print(f"{'Outcome':<18} {'Prob':>6} {'Odds':>6} {'Kelly%':>8} {'Bet':>8} {'EV/unit':>9} {'Edge':>6}")
    print("-" * 67)
    for r in results:
        edge_str = "YES" if r["has_edge"] else "-"
        print(
            f"{r['outcome']:<18} "
            f"{r['prob']:>6.1%} "
            f"{r['odds']:>6.2f} "
            f"{r['kelly_f']:>8.2%} "
            f"${r['bet']:>7.2f} "
            f"{r['ev_per_unit']:>+9.4f} "
            f"{edge_str:>6}"
        )


if __name__ == "__main__":
    main()
