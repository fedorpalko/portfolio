#!/usr/bin/env bash
# =============================================================================
# backtest_runner.sh — KC_Breakout multi-regime backtest pipeline
# =============================================================================
# Usage:
#   chmod +x backtest_runner.sh
#   ./backtest_runner.sh
#
# Market regimes tested:
#   1. Bull Run         20200101-20211130  BTC $8k → $69k, parabolic
#   2. Bear Market      20211201-20221231  BTC $69k → $15.5k, -78% drawdown
#   3. Accumulation     20230101-20230930  BTC $16.5k → $26k, low volatility
#   4. Pre-Halving Bull 20231001-20240331  BTC $26k → $73k, strong trend
#   5. Post-Halving     20240401-20241231  BTC $73k → ATH, institutional driven
#
# Each regime downloads fresh data, runs a backtest, and logs results.
# All output is aggregated into a single timestamped results file.
# =============================================================================

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────

STRATEGY="KC_Breakout"
TIMEFRAME="4h"
FT="docker compose run --rm freqtrade"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="./backtest_results"
RESULTS_FILE="${RESULTS_DIR}/${STRATEGY}_multi_regime_${TIMESTAMP}.txt"

mkdir -p "$RESULTS_DIR"

# ── Regime definitions ────────────────────────────────────────────────────────
# Format: "LABEL|TIMERANGE|DESCRIPTION"

declare -a REGIMES=(
    "BULL_RUN|20200101-20211130|Bull Run 2020-2021 — BTC 8k to 69k, parabolic institutional rally"
    "BEAR_MARKET|20211201-20221231|Bear Market 2022 — BTC 69k to 15.5k, -78% drawdown"
    "ACCUMULATION|20230101-20230930|Accumulation 2023 — BTC 16.5k to 26k, low volatility grind"
    "PRE_HALVING|20231001-20240331|Pre-Halving Bull 2023-2024 — BTC 26k to 73k, strong trend"
    "POST_HALVING|20240401-20241231|Post-Halving 2024 — BTC 73k to ATH, institutional driven"
)

# ── Helpers ───────────────────────────────────────────────────────────────────

log() {
    echo "[$(date +"%H:%M:%S")] $1"
    echo "[$(date +"%H:%M:%S")] $1" >> "$RESULTS_FILE"
}

divider() {
    local line="================================================================="
    echo "$line" | tee -a "$RESULTS_FILE"
}

thin_divider() {
    local line="-----------------------------------------------------------------"
    echo "$line" | tee -a "$RESULTS_FILE"
}

tee_log() {
    tee -a "$RESULTS_FILE"
}

# ── Master header ─────────────────────────────────────────────────────────────

divider
{
    echo ""
    echo "  KC_Breakout — Multi-Regime Backtest Pipeline"
    echo "  Strategy  : $STRATEGY"
    echo "  Timeframe : $TIMEFRAME"
    echo "  Regimes   : ${#REGIMES[@]}"
    echo "  Run at    : $(date)"
    echo ""
} | tee_log
divider

# ── Regime loop ───────────────────────────────────────────────────────────────

REGIME_NUM=0

for regime in "${REGIMES[@]}"; do
    REGIME_NUM=$((REGIME_NUM + 1))

    IFS='|' read -r LABEL TIMERANGE DESCRIPTION <<< "$regime"

    echo "" | tee_log
    divider
    {
        echo ""
        echo "  REGIME ${REGIME_NUM}/${#REGIMES[@]} — ${LABEL}"
        echo "  ${DESCRIPTION}"
        echo "  Timerange : ${TIMERANGE}"
        echo ""
    } | tee_log
    divider

    # Step 1 — Download data for this regime
    log "Downloading data for ${LABEL} (${TIMERANGE})..."
    thin_divider
    {
        $FT download-data \
            --timerange "$TIMERANGE" \
            --timeframe "$TIMEFRAME" \
            --erase 2>&1
    } | tee_log

    log "Download complete for ${LABEL}."
    thin_divider

    # Step 2 — Run backtest for this regime
    log "Running backtest for ${LABEL}..."
    thin_divider
    {
        $FT backtesting \
            --strategy "$STRATEGY" \
            --timerange "$TIMERANGE" \
            --timeframe "$TIMEFRAME" 2>&1
    } | tee_log

    log "Backtest complete for ${LABEL}."
    divider

done

# ── Summary footer ────────────────────────────────────────────────────────────

echo "" | tee_log
divider
{
    echo ""
    echo "  ALL REGIMES COMPLETE"
    echo "  Strategy  : $STRATEGY"
    echo "  Timeframe : $TIMEFRAME"
    echo "  Finished  : $(date)"
    echo "  Results   : $RESULTS_FILE"
    echo ""
    echo "  Regimes run:"
    for regime in "${REGIMES[@]}"; do
        IFS='|' read -r LABEL TIMERANGE DESCRIPTION <<< "$regime"
        echo "    [${LABEL}] ${TIMERANGE}"
    done
    echo ""
} | tee_log
divider

echo ""
echo "Done. Full output saved to: $RESULTS_FILE"
