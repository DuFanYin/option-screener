#ifndef OBJECT_HPP
#define OBJECT_HPP

#include <string>
#include <optional>
#include <vector>
#include <tuple>

// ===================== OPTION =====================
struct Option {
    std::string symbol;
    std::string expiry;
    double strike;
    std::string side;  // "CALL" or "PUT"

    double mid;
    double iv;
    double volume;
    double oi;

    double delta;
    double gamma;
    double theta;
    double vega;
    double rho;
    int days_to_expiry;

    std::optional<double> bid;
    std::optional<double> ask;

    bool is_call() const { return side == "CALL"; }
    bool is_put() const { return side == "PUT"; }

    bool is_otm(double spot) const {
        return (is_call() && strike > spot) || (is_put() && strike < spot);
    }

    double price() const { return mid > 0.0 ? mid : 0.0; }
    double mid_price() const { return price(); }
    double liquidity() const { return volume + oi; }

    std::optional<double> bid_ask_spread() const {
        if (bid.has_value() && ask.has_value()) {
            return std::abs(*ask - *bid);
        }
        return std::nullopt;
    }

    std::optional<double> volume_ratio() const {
        if (oi > 0) {
            return volume / oi;
        }
        return std::nullopt;
    }

    std::string to_string() const {
        return side + " " + std::to_string(strike) + " exp=" + expiry + 
               " mid=" + std::to_string(mid) + " Δ=" + std::to_string(delta);
    }
};

// ===================== DIRECTION =====================
enum class Direction {
    LONG,
    SHORT
};

inline std::string direction_to_string(Direction dir) {
    return dir == Direction::LONG ? "LONG" : "SHORT";
}

// ===================== STRATEGY FILTER =====================
struct StrategyFilter {
    bool single_calls = false;
    bool iron_condors = false;
    bool straddles = false;
    bool strangles = false;
};

// ===================== CONFIG FILTER =====================
struct ConfigFilter {
    // Option-level filters
    std::optional<int> min_volume;
    std::optional<int> min_oi;
    std::optional<double> min_price;
    std::optional<std::string> expiry;
    std::optional<std::tuple<int, int>> days_to_expiry_range;
    std::optional<std::tuple<double, double>> volume_ratio_range;
    std::optional<double> max_bid_ask_spread;

    // Strategy-level filters
    std::optional<Direction> direction;
    std::optional<std::tuple<double, double>> debit_range;
    std::optional<std::tuple<double, double>> credit_range;
    std::optional<std::tuple<double, double>> potential_gain_range;
    std::optional<std::tuple<double, double>> potential_loss_range;
    std::optional<std::tuple<double, double>> rr_range;
    std::optional<std::tuple<double, double>> net_delta_range;
    std::optional<std::tuple<double, double>> net_theta_range;
    std::optional<std::tuple<double, double>> net_vega_range;
    std::optional<std::tuple<double, double>> iv_range;
};

#endif // OBJECT_HPP

