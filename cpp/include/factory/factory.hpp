#ifndef FACTORY_HPP
#define FACTORY_HPP

#include "object.hpp"
#include "strategy/generator_class.hpp"
#include "strategy/strategy_class.hpp"
#include <vector>
#include <memory>
#include <string>
#include <algorithm>
#include <map>
#include <iostream>
#include <iomanip>
#include <cmath>
#include <cstdio>

class StrategyList {
public:
    StrategyList(std::vector<std::unique_ptr<Strategy>>&& strategies)
        : strategies_(std::move(strategies)) {}

    StrategyList rank(const std::string& key = "rr", bool reverse = true) {
        if (strategies_.empty()) {
            return StrategyList(std::vector<std::unique_ptr<Strategy>>());
        }

        std::vector<std::unique_ptr<Strategy>> sorted = [&]() {
            auto copy = clone();
            
            if (key == "rr") {
                std::sort(copy.begin(), copy.end(), 
                    [&](const auto& a, const auto& b) { 
                        return reverse ? (a->rr() > b->rr()) : (a->rr() < b->rr());
                    });
            } else if (key == "gain") {
                std::sort(copy.begin(), copy.end(),
                    [&](const auto& a, const auto& b) {
                        return reverse ? (a->max_gain() > b->max_gain()) : (a->max_gain() < b->max_gain());
                    });
            } else if (key == "loss") {
                std::sort(copy.begin(), copy.end(),
                    [](const auto& a, const auto& b) {
                        return a->max_loss() < b->max_loss();
                    });
            } else if (key == "cost") {
                std::sort(copy.begin(), copy.end(),
                    [&](const auto& a, const auto& b) {
                        return reverse ? (a->cost() > b->cost()) : (a->cost() < b->cost());
                    });
            }
            
            return copy;
        }();

        return StrategyList(std::move(sorted));
    }

    StrategyList top(size_t n = 10) {
        n = std::min(n, strategies_.size());
        std::vector<std::unique_ptr<Strategy>> result;
        for (size_t i = 0; i < n; ++i) {
            result.push_back(clone_strategy(*strategies_[i]));
        }
        return StrategyList(std::move(result));
    }

    size_t size() const { return strategies_.size(); }

    void print() const {
        if (strategies_.empty()) {
            std::cout << "No strategies found." << std::endl;
            return;
        }

        // Print header
        std::printf("%-5s %-50s %12s %12s %12s %12s %18s %18s %18s %18s\n",
                    "", "strategy", "cost", "max_gain", "max_loss", "rr",
                    "delta", "theta", "vega", "iv");
        
        // Print separator
        std::cout << std::string(165, '-') << std::endl;

        // Print each strategy
        for (size_t i = 0; i < strategies_.size(); ++i) {
            const auto& s = strategies_[i];
            
            auto avg_iv = s->avg_iv();
            double theta_val = s->net_theta();
            // Use scientific notation for theta when very small or very large
            bool use_scientific_theta = (std::abs(theta_val) < 0.001 && theta_val != 0.0) || 
                                       std::abs(theta_val) >= 1000.0;

            // Print row number and strategy name
            std::printf("%-5zu %-50s ", i, s->pretty().c_str());
            
            // Print cost
            std::printf("%12.1f ", s->cost());
            
            // Print max_gain (infinity or number)
            if (std::isinf(s->max_gain())) {
                std::printf("%12s ", "inf");
            } else {
                std::printf("%12.1f ", s->max_gain());
            }
            
            // Print max_loss (infinity or number)
            if (std::isinf(s->max_loss())) {
                std::printf("%12s ", "inf");
            } else {
                std::printf("%12.1f ", s->max_loss());
            }
            
            // Print rr (infinity or number)
            if (std::isinf(s->rr())) {
                std::printf("%12s ", "inf");
            } else {
                std::printf("%12.2f ", s->rr());
            }
            
            // Print delta (always fixed point)
            std::printf("%18.6f ", s->net_delta());
            
            // Print theta (scientific for small/large values)
            if (use_scientific_theta) {
                std::printf("%18.6e ", theta_val);
            } else {
                std::printf("%18.6f ", theta_val);
            }
            
            // Print vega (always fixed point)
            std::printf("%18.6f ", s->net_vega());
            
            // Print iv (nan or number)
            if (avg_iv.has_value()) {
                std::printf("%18.6f", avg_iv.value());
            } else {
                std::printf("%18s", "nan");
            }
            
            std::cout << std::endl;
        }
    }

private:
    std::vector<std::unique_ptr<Strategy>> strategies_;

    std::vector<std::unique_ptr<Strategy>> clone() {
        std::vector<std::unique_ptr<Strategy>> result;
        for (const auto& s : strategies_) {
            result.push_back(clone_strategy(*s));
        }
        return result;
    }

    std::unique_ptr<Strategy> clone_strategy(const Strategy& s) {
        // Clone strategy based on type
        if (auto* st = dynamic_cast<const SingleLeg*>(&s)) {
            auto legs = s.legs();
            std::string action = s.leg_sign(legs[0]);
            return std::make_unique<SingleLeg>(legs[0], action, s.direction);
        }
        if (auto* st = dynamic_cast<const IronCondor*>(&s)) {
            auto legs = s.legs();
            // IronCondor constructor: sc, bc, sp, bp
            // legs() returns: sc, bc, sp, bp
            return std::make_unique<IronCondor>(legs[0], legs[1], legs[2], legs[3], s.direction);
        }
        if (auto* st = dynamic_cast<const Straddle*>(&s)) {
            auto legs = s.legs();
            // Straddle constructor: call, put
            // Identify call and put by side
            Option call, put;
            for (const auto& leg : legs) {
                if (leg.is_call()) call = leg;
                if (leg.is_put()) put = leg;
            }
            return std::make_unique<Straddle>(call, put, s.direction);
        }
        if (auto* st = dynamic_cast<const Strangle*>(&s)) {
            auto legs = s.legs();
            // Strangle constructor: call, put
            // Identify call and put by side
            Option call, put;
            for (const auto& leg : legs) {
                if (leg.is_call()) call = leg;
                if (leg.is_put()) put = leg;
            }
            return std::make_unique<Strangle>(call, put, s.direction);
        }
        return nullptr;
    }
};

class StrategyFactory {
public:
    StrategyFactory(const std::vector<Option>& options, double spot)
        : options_(options), spot_(spot) {
        generators_["single_calls"] = std::make_unique<SingleCallsGenerator>(options, spot);
        generators_["iron_condors"] = std::make_unique<IronCondorsGenerator>(options, spot);
        generators_["straddles"] = std::make_unique<StraddlesGenerator>(options, spot);
        generators_["strangles"] = std::make_unique<StranglesGenerator>(options, spot);
    }

    StrategyList strategy(const StrategyFilter& s_filter, const ConfigFilter& c_filter) {
        return generate(s_filter, c_filter);
    }

    StrategyList generate(const StrategyFilter& s_filter, const ConfigFilter& c_filter) {
        std::vector<std::unique_ptr<Strategy>> all_strategies;

        if (s_filter.single_calls) {
            auto strategies = generators_["single_calls"]->generate(c_filter);
            auto filtered = filter_strategies(std::move(strategies), c_filter);
            all_strategies.insert(all_strategies.end(),
                std::make_move_iterator(filtered.begin()),
                std::make_move_iterator(filtered.end()));
        }

        if (s_filter.iron_condors) {
            auto strategies = generators_["iron_condors"]->generate(c_filter);
            auto filtered = filter_strategies(std::move(strategies), c_filter);
            all_strategies.insert(all_strategies.end(),
                std::make_move_iterator(filtered.begin()),
                std::make_move_iterator(filtered.end()));
        }

        if (s_filter.straddles) {
            auto strategies = generators_["straddles"]->generate(c_filter);
            auto filtered = filter_strategies(std::move(strategies), c_filter);
            all_strategies.insert(all_strategies.end(),
                std::make_move_iterator(filtered.begin()),
                std::make_move_iterator(filtered.end()));
        }

        if (s_filter.strangles) {
            auto strategies = generators_["strangles"]->generate(c_filter);
            auto filtered = filter_strategies(std::move(strategies), c_filter);
            all_strategies.insert(all_strategies.end(),
                std::make_move_iterator(filtered.begin()),
                std::make_move_iterator(filtered.end()));
        }

        return StrategyList(std::move(all_strategies));
    }

private:
    const std::vector<Option>& options_;
    double spot_;
    std::map<std::string, std::unique_ptr<StrategyGenerator>> generators_;

    static bool check_range(double value, const std::optional<std::tuple<double, double>>& range) {
        if (!range.has_value()) return true;
        
        // Handle NaN - NaN cannot be in any range
        if (std::isnan(value)) return false;
        
        auto [min_val, max_val] = range.value();
        // Inclusive range check: min_val <= value <= max_val
        // Infinity values are handled correctly by normal comparison:
        // - inf <= finite_max is false, so inf outside finite range is correctly excluded
        // - inf <= inf is true, so inf can be allowed if range includes infinity
        return value >= min_val && value <= max_val;
    }

    std::vector<std::unique_ptr<Strategy>> filter_strategies(
        std::vector<std::unique_ptr<Strategy>> strategies,
        const ConfigFilter& c_filter) {
        
        std::vector<std::unique_ptr<Strategy>> filtered;

        for (auto& strategy : strategies) {
            if (c_filter.debit_range.has_value() && strategy->debit() > 0) {
                if (!check_range(strategy->debit(), c_filter.debit_range)) {
                    continue;
                }
            }

            if (c_filter.credit_range.has_value() && strategy->credit() > 0) {
                if (!check_range(strategy->credit(), c_filter.credit_range)) {
                    continue;
                }
            }

            if (!check_range(strategy->max_gain(), c_filter.potential_gain_range) ||
                !check_range(strategy->max_loss(), c_filter.potential_loss_range) ||
                !check_range(strategy->rr(), c_filter.rr_range) ||
                !check_range(strategy->net_delta(), c_filter.net_delta_range) ||
                !check_range(strategy->net_theta(), c_filter.net_theta_range) ||
                !check_range(strategy->net_vega(), c_filter.net_vega_range)) {
                continue;
            }

            auto avg_iv = strategy->avg_iv();
            if (avg_iv.has_value() && !check_range(avg_iv.value(), c_filter.iv_range)) {
                continue;
            }

            filtered.push_back(std::move(strategy));
        }

        return filtered;
    }
};

#endif // FACTORY_HPP

