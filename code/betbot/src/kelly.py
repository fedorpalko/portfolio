# This file calculates Kelly Criterion based on inputted odds and probabilities to win


def kelly_pos_sizing_simple(prob, odds):
    edge = prob * odds - 1
    if edge <= 0:
        return 0  # can't bet, no edge here
    f = edge / (odds - 1)
    return max(0, f)  # returns the ideal kelly fraction, ensures we don't bet negative


def kelly_bet_sizing_simple(
    bankroll, prob1, probx, prob2, odds1, oddsx, odds2, fractional_kelly=0.25
):
    kelly_1 = kelly_pos_sizing_simple(prob1, odds1)
    kelly_x = kelly_pos_sizing_simple(probx, oddsx)
    kelly_2 = kelly_pos_sizing_simple(prob2, odds2)

    best_outcome = max(
        [("1", kelly_1), ("x", kelly_x), ("2", kelly_2)], key=lambda x: x[1]
    )

    if best_outcome[1] <= 0:
        return {}  # no edge on anything

    bet_size = best_outcome[1] * fractional_kelly * bankroll
    return {best_outcome[0]: bet_size}
