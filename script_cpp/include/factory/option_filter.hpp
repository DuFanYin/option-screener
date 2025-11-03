#ifndef OPTION_FILTER_HPP
#define OPTION_FILTER_HPP

#include "object.hpp"
#include <vector>
#include <functional>
#include <algorithm>
#include <tuple>

class OptionFilter {
public:
    OptionFilter(std::vector<Option>& universe, double spot)
        : universe_(universe), spot_(spot) {}

    OptionFilter& filter(std::function<bool(const Option&)> cond) {
        std::vector<Option> filtered;
        for (const auto& opt : universe_) {
            if (cond(opt)) {
                filtered.push_back(opt);
            }
        }
        universe_ = std::move(filtered);
        return *this;
    }

    OptionFilter& apply_filter(const ConfigFilter& cfg) {
        if (cfg.min_volume.has_value()) {
            filter([&](const Option& o) { 
                return (o.volume >= cfg.min_volume.value()); 
            });
        }

        if (cfg.min_oi.has_value()) {
            filter([&](const Option& o) { 
                return (o.oi >= cfg.min_oi.value()); 
            });
        }

        if (cfg.min_price.has_value()) {
            filter([&](const Option& o) { 
                return (o.price() >= cfg.min_price.value()); 
            });
        }

        if (cfg.expiry.has_value()) {
            filter([&](const Option& o) { 
                return o.expiry == cfg.expiry.value(); 
            });
        }

        if (cfg.days_to_expiry_range.has_value()) {
            auto range = cfg.days_to_expiry_range.value();
            auto min_days = std::get<0>(range);
            auto max_days = std::get<1>(range);
            filter([min_days, max_days](const Option& o) { 
                return o.days_to_expiry >= min_days && 
                       o.days_to_expiry <= max_days; 
            });
        }

        if (cfg.volume_ratio_range.has_value()) {
            auto range = cfg.volume_ratio_range.value();
            auto min_ratio = std::get<0>(range);
            auto max_ratio = std::get<1>(range);
            filter([min_ratio, max_ratio](const Option& o) { 
                auto ratio = o.volume_ratio();
                return ratio.has_value() && 
                       *ratio >= min_ratio && *ratio <= max_ratio; 
            });
        }

        if (cfg.max_bid_ask_spread.has_value()) {
            filter([&](const Option& o) { 
                auto spread = o.bid_ask_spread();
                return spread.has_value() && 
                       *spread <= cfg.max_bid_ask_spread.value(); 
            });
        }

        return *this;
    }

    std::vector<Option>& result() { return universe_; }

private:
    std::vector<Option>& universe_;
    double spot_;
};

#endif // OPTION_FILTER_HPP

