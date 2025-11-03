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

// ===================== SINGLE CALLS GENERATOR =====================
class SingleCallsGenerator : public StrategyGenerator {
public:
    using StrategyGenerator::StrategyGenerator;

    std::vector<std::unique_ptr<Strategy>> generate(const ConfigFilter& cfg) override {
        std::vector<Option> opts = OptionFilter(
            const_cast<std::vector<Option>&>(options_), spot_
        ).apply_filter(cfg).result();

        // Filter to only calls and OTM
        std::vector<Option> filtered_opts;
        for (const auto& opt : opts) {
            if (opt.is_call() && opt.is_otm(spot_)) {
                filtered_opts.push_back(opt);
            }
        }

        std::string direction_str = direction_to_string(cfg.direction.value());
        std::string action = (direction_str == "SHORT") ? "SELL" : "BUY";

        std::vector<std::unique_ptr<Strategy>> strategies;
        for (const auto& opt : filtered_opts) {
            strategies.push_back(
                std::make_unique<SingleLeg>(opt, action, direction_str)
            );
        }

        return strategies;
    }
};

// ===================== IRON CONDORS GENERATOR =====================
class IronCondorsGenerator : public StrategyGenerator {
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

            // Short calls are above spot
            std::vector<Option> short_calls;
            for (const auto& c : calls) {
                if (c.strike > spot_) {
                    short_calls.push_back(c);
                }
            }

            // Short puts are below spot
            std::vector<Option> short_puts;
            for (const auto& p : puts) {
                if (p.strike < spot_) {
                    short_puts.push_back(p);
                }
            }

            // Generate iron condor combinations
            for (const auto& short_call : short_calls) {
                // Buy calls above short call
                std::vector<Option> buy_calls;
                for (const auto& c : calls) {
                    if (c.strike > short_call.strike) {
                        buy_calls.push_back(c);
                    }
                }

                for (const auto& buy_call : buy_calls) {
                    for (const auto& short_put : short_puts) {
                        // Buy puts below short put
                        std::vector<Option> buy_puts;
                        for (const auto& p : puts) {
                            if (p.strike < short_put.strike) {
                                buy_puts.push_back(p);
                            }
                        }

                        for (const auto& buy_put : buy_puts) {
                            strategies.push_back(
                                std::make_unique<IronCondor>(
                                    short_call, buy_call, short_put, buy_put, direction_str
                                )
                            );
                        }
                    }
                }
            }
        }

        return strategies;
    }
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

// ===================== STRANGLES GENERATOR =====================
class StranglesGenerator : public StrategyGenerator {
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
            // OTM calls (strike > spot)
            std::vector<Option> calls;
            for (const auto& opt : chain) {
                if (opt.is_call() && opt.strike > spot_) {
                    calls.push_back(opt);
                }
            }

            // OTM puts (strike < spot)
            std::vector<Option> puts;
            for (const auto& opt : chain) {
                if (opt.is_put() && opt.strike < spot_) {
                    puts.push_back(opt);
                }
            }

            std::sort(calls.begin(), calls.end(), 
                [](const Option& a, const Option& b) { return a.strike < b.strike; });
            std::sort(puts.begin(), puts.end(), 
                [](const Option& a, const Option& b) { return a.strike < b.strike; });

            // Generate strangle combinations: OTM call + OTM put
            for (const auto& call : calls) {
                for (const auto& put : puts) {
                    strategies.push_back(
                        std::make_unique<Strangle>(call, put, direction_str)
                    );
                }
            }
        }

        return strategies;
    }
};

#endif // GENERATOR_CLASS_HPP

