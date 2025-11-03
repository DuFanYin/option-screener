#include "config.hpp"
#include <fstream>
#include <json.hpp>
#include <sstream>
#include <stdexcept>

using json = nlohmann::json;

static Direction string_to_direction(const std::string& str) {
    if (str == "LONG" || str == "long") {
        return Direction::LONG;
    }
    return Direction::SHORT;
}

ConfigFilter ConfigLoader::load_from_json(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open config file: " + path);
    }

    json config_json;
    file >> config_json;
    
    // Get config_filter section
    json config;
    if (config_json.contains("config_filter")) {
        config = config_json["config_filter"];
    } else {
        config = config_json;  // If no nested structure, use root
    }

    ConfigFilter cfg;

    // Option-level filters
    if (config.contains("min_volume") && !config["min_volume"].is_null()) {
        cfg.min_volume = config["min_volume"].get<int>();
    }
    if (config.contains("min_oi") && !config["min_oi"].is_null()) {
        cfg.min_oi = config["min_oi"].get<int>();
    }
    if (config.contains("min_price") && !config["min_price"].is_null()) {
        cfg.min_price = config["min_price"].get<double>();
    }
    if (config.contains("expiry") && !config["expiry"].is_null()) {
        cfg.expiry = config["expiry"].get<std::string>();
    }
    if (config.contains("days_to_expiry_range") && !config["days_to_expiry_range"].is_null()) {
        auto range = config["days_to_expiry_range"];
        cfg.days_to_expiry_range = std::make_tuple(
            range[0].get<int>(),
            range[1].get<int>()
        );
    }
    if (config.contains("volume_ratio_range") && !config["volume_ratio_range"].is_null()) {
        auto range = config["volume_ratio_range"];
        cfg.volume_ratio_range = std::make_tuple(
            range[0].get<double>(),
            range[1].get<double>()
        );
    }
    if (config.contains("max_bid_ask_spread") && !config["max_bid_ask_spread"].is_null()) {
        cfg.max_bid_ask_spread = config["max_bid_ask_spread"].get<double>();
    }

    // Strategy-level filters
    if (config.contains("direction") && !config["direction"].is_null()) {
        cfg.direction = string_to_direction(config["direction"].get<std::string>());
    }
    if (config.contains("debit_range") && !config["debit_range"].is_null()) {
        auto range = config["debit_range"];
        cfg.debit_range = std::make_tuple(
            range[0].get<double>(),
            range[1].get<double>()
        );
    }
    if (config.contains("credit_range") && !config["credit_range"].is_null()) {
        auto range = config["credit_range"];
        cfg.credit_range = std::make_tuple(
            range[0].get<double>(),
            range[1].get<double>()
        );
    }
    if (config.contains("potential_gain_range") && !config["potential_gain_range"].is_null()) {
        auto range = config["potential_gain_range"];
        cfg.potential_gain_range = std::make_tuple(
            range[0].get<double>(),
            range[1].get<double>()
        );
    }
    if (config.contains("potential_loss_range") && !config["potential_loss_range"].is_null()) {
        auto range = config["potential_loss_range"];
        cfg.potential_loss_range = std::make_tuple(
            range[0].get<double>(),
            range[1].get<double>()
        );
    }
    if (config.contains("rr_range") && !config["rr_range"].is_null()) {
        auto range = config["rr_range"];
        cfg.rr_range = std::make_tuple(
            range[0].get<double>(),
            range[1].get<double>()
        );
    }
    if (config.contains("net_delta_range") && !config["net_delta_range"].is_null()) {
        auto range = config["net_delta_range"];
        cfg.net_delta_range = std::make_tuple(
            range[0].get<double>(),
            range[1].get<double>()
        );
    }
    if (config.contains("net_theta_range") && !config["net_theta_range"].is_null()) {
        auto range = config["net_theta_range"];
        cfg.net_theta_range = std::make_tuple(
            range[0].get<double>(),
            range[1].get<double>()
        );
    }
    if (config.contains("net_vega_range") && !config["net_vega_range"].is_null()) {
        auto range = config["net_vega_range"];
        cfg.net_vega_range = std::make_tuple(
            range[0].get<double>(),
            range[1].get<double>()
        );
    }
    if (config.contains("iv_range") && !config["iv_range"].is_null()) {
        auto range = config["iv_range"];
        cfg.iv_range = std::make_tuple(
            range[0].get<double>(),
            range[1].get<double>()
        );
    }

    return cfg;
}

StrategyFilter ConfigLoader::load_strategy_filter_from_json(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open config file: " + path);
    }

    json config_json;
    file >> config_json;

    StrategyFilter s_filter;
    
    json sf;
    if (config_json.contains("strategy_filter")) {
        sf = config_json["strategy_filter"];
        if (sf.contains("single_calls")) {
            s_filter.single_calls = sf["single_calls"].get<bool>();
        }
        if (sf.contains("iron_condors")) {
            s_filter.iron_condors = sf["iron_condors"].get<bool>();
        }
        if (sf.contains("straddles")) {
            s_filter.straddles = sf["straddles"].get<bool>();
        }
        if (sf.contains("strangles")) {
            s_filter.strangles = sf["strangles"].get<bool>();
        }
    } else {
        // If no nested structure, try root level
        sf = config_json;
        if (sf.contains("single_calls")) {
            s_filter.single_calls = sf["single_calls"].get<bool>();
        }
        if (sf.contains("iron_condors")) {
            s_filter.iron_condors = sf["iron_condors"].get<bool>();
        }
        if (sf.contains("straddles")) {
            s_filter.straddles = sf["straddles"].get<bool>();
        }
        if (sf.contains("strangles")) {
            s_filter.strangles = sf["strangles"].get<bool>();
        }
    }

    return s_filter;
}

