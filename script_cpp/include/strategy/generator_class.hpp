#ifndef GENERATOR_CLASS_HPP
#define GENERATOR_CLASS_HPP

#include "object.hpp"
#include "factory/option_filter.hpp"
#include "strategy/strategy_class.hpp"
#include <vector>
#include <memory>
#include <map>
#include <algorithm>
#include <string>

// ===================== STRATEGY GENERATORS =====================
class StrategyGenerator {
public:
    StrategyGenerator(const std::vector<Option>& options, double spot)
        : options_(options), spot_(spot) {}
    virtual ~StrategyGenerator() = default;

    virtual std::vector<std::unique_ptr<Strategy>> generate(const ConfigFilter& cfg) = 0;

protected:
    const std::vector<Option>& options_;
    double spot_;
};

// ===================== STRADDLES GENERATOR =====================
class StraddlesGenerator : public StrategyGenerator {
public:
    using StrategyGenerator::StrategyGenerator;

    std::vector<std::unique_ptr<Strategy>> generate(const ConfigFilter& cfg) override {
        std::vector<Option> opts = OptionFilter(
            const_cast<std::vector<Option>&>(options_), spot_
        ).apply_filter(cfg).result();

        std::string direction_str = direction_to_string(cfg.direction.value());

        // Group by expiry
        std::map<std::string, std::vector<Option>> expiry_map;
        for (const auto& opt : opts) {
            expiry_map[opt.expiry].push_back(opt);
        }

        std::vector<std::unique_ptr<Strategy>> strategies;
        for (auto& [expiry, chain] : expiry_map) {
            std::vector<Option> calls, puts;
            for (const auto& opt : chain) {
                if (opt.is_call()) calls.push_back(opt);
                if (opt.is_put()) puts.push_back(opt);
            }

            std::sort(calls.begin(), calls.end(), 
                [](const Option& a, const Option& b) { return a.strike < b.strike; });
            std::sort(puts.begin(), puts.end(), 
                [](const Option& a, const Option& b) { return a.strike < b.strike; });

            // Find call and put at same strike
            for (const auto& call : calls) {
                for (const auto& put : puts) {
                    if (call.strike == put.strike) {
                        strategies.push_back(
                            std::make_unique<Straddle>(call, put, direction_str)
                        );
                    }
                }
            }
        }

        return strategies;
    }
};

#endif // GENERATOR_CLASS_HPP

