#ifndef STRATEGY_CLASS_HPP
#define STRATEGY_CLASS_HPP

#include "object.hpp"
#include <vector>
#include <memory>
#include <string>
#include <limits>
#include <optional>

// ===================== BASE STRATEGY =====================
class Strategy {
public:
    std::string direction;  // "LONG" or "SHORT"

    Strategy(const std::string& dir) : direction(dir) {}
    virtual ~Strategy() = default;

    virtual std::vector<Option> legs() const = 0;
    virtual double debit() const = 0;
    virtual double credit() const = 0;
    virtual double max_gain() const = 0;
    virtual double max_loss() const = 0;
    virtual std::string pretty() const = 0;

    double cost() const {
        return debit() - credit();
    }

    double rr() const {
        double loss = max_loss();
        return loss > 0 ? (max_gain() / loss) : std::numeric_limits<double>::infinity();
    }

    double net_delta() const {
        double total = 0.0;
        for (const auto& [leg, qty] : signed_legs()) {
            total += leg.delta * 100.0 * qty;
        }
        return total;
    }

    double net_theta() const {
        double total = 0.0;
        for (const auto& [leg, qty] : signed_legs()) {
            total += leg.theta * 100.0 * qty;
        }
        return total;
    }

    double net_vega() const {
        double total = 0.0;
        for (const auto& [leg, qty] : signed_legs()) {
            total += leg.vega * 100.0 * qty;
        }
        return total;
    }

    std::optional<double> avg_iv() const {
        std::vector<double> ivs;
        for (const auto& [leg, qty] : signed_legs()) {
            if (leg.iv > 0) {
                ivs.push_back(leg.iv);
            }
        }
        if (ivs.empty()) return std::nullopt;
        
        double sum = 0.0;
        for (double iv : ivs) sum += iv;
        return sum / ivs.size();
    }

protected:
    virtual std::string leg_sign(const Option& leg) const = 0;

    std::vector<std::pair<Option, int>> signed_legs() const {
        std::vector<std::pair<Option, int>> result;
        for (const Option& leg : legs()) {
            int qty = (leg_sign(leg) == "BUY") ? 1 : -1;
            result.emplace_back(leg, qty);
        }
        return result;
    }
};

// ===================== STRADDLE =====================
class Straddle : public Strategy {
public:
    Straddle(const Option& call, const Option& put, const std::string& direction)
        : Strategy(direction), call_(call), put_(put) {}

    std::vector<Option> legs() const override {
        return {call_, put_};
    }

    std::string leg_sign(const Option& leg) const override {
        return direction == "LONG" ? "BUY" : "SELL";
    }

    double debit() const override {
        double total = (call_.price() + put_.price()) * 100.0;
        return direction == "LONG" ? total : 0.0;
    }

    double credit() const override {
        double total = (call_.price() + put_.price()) * 100.0;
        return direction == "SHORT" ? total : 0.0;
    }

    double max_gain() const override {
        if (direction == "LONG") {
            return std::numeric_limits<double>::infinity();
        }
        return credit();
    }

    double max_loss() const override {
        if (direction == "LONG") {
            return cost();
        }
        return std::numeric_limits<double>::infinity();
    }

    std::string pretty() const override {
        return "Straddle " + direction + " C:" + std::to_string(call_.strike) + 
               " P:" + std::to_string(put_.strike) + " exp " + call_.expiry;
    }

private:
    Option call_;
    Option put_;
};

#endif // STRATEGY_CLASS_HPP

