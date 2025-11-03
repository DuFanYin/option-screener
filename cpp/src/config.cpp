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
    json config = config_json["config_filter"];

    ConfigFilter cfg;

    // Option-level filters
    cfg.min_volume = config["min_volume"].is_null() ? std::nullopt : std::make_optional(config["min_volume"].get<int>());
    cfg.min_oi = config["min_oi"].is_null() ? std::nullopt : std::make_optional(config["min_oi"].get<int>());
    cfg.min_price = config["min_price"].is_null() ? std::nullopt : std::make_optional(config["min_price"].get<double>());
    cfg.expiry = config["expiry"].is_null() ? std::nullopt : std::make_optional(config["expiry"].get<std::string>());
    
    if (!config["days_to_expiry_range"].is_null()) {
        auto range = config["days_to_expiry_range"];
        cfg.days_to_expiry_range = std::make_tuple(range[0].get<int>(), range[1].get<int>());
    }
    if (!config["volume_ratio_range"].is_null()) {
        auto range = config["volume_ratio_range"];
        cfg.volume_ratio_range = std::make_tuple(range[0].get<double>(), range[1].get<double>());
    }
    cfg.max_bid_ask_spread = config["max_bid_ask_spread"].is_null() ? std::nullopt : std::make_optional(config["max_bid_ask_spread"].get<double>());

    // Strategy-level filters
    cfg.direction = config["direction"].is_null() ? std::nullopt : std::make_optional(string_to_direction(config["direction"].get<std::string>()));
    
    if (!config["debit_range"].is_null()) {
        auto range = config["debit_range"];
        cfg.debit_range = std::make_tuple(range[0].get<double>(), range[1].get<double>());
    }
    if (!config["credit_range"].is_null()) {
        auto range = config["credit_range"];
        cfg.credit_range = std::make_tuple(range[0].get<double>(), range[1].get<double>());
    }
    if (!config["potential_gain_range"].is_null()) {
        auto range = config["potential_gain_range"];
        cfg.potential_gain_range = std::make_tuple(range[0].get<double>(), range[1].get<double>());
    }
    if (!config["potential_loss_range"].is_null()) {
        auto range = config["potential_loss_range"];
        cfg.potential_loss_range = std::make_tuple(range[0].get<double>(), range[1].get<double>());
    }
    if (!config["rr_range"].is_null()) {
        auto range = config["rr_range"];
        cfg.rr_range = std::make_tuple(range[0].get<double>(), range[1].get<double>());
    }
    if (!config["net_delta_range"].is_null()) {
        auto range = config["net_delta_range"];
        cfg.net_delta_range = std::make_tuple(range[0].get<double>(), range[1].get<double>());
    }
    if (!config["net_theta_range"].is_null()) {
        auto range = config["net_theta_range"];
        cfg.net_theta_range = std::make_tuple(range[0].get<double>(), range[1].get<double>());
    }
    if (!config["net_vega_range"].is_null()) {
        auto range = config["net_vega_range"];
        cfg.net_vega_range = std::make_tuple(range[0].get<double>(), range[1].get<double>());
    }
    if (!config["iv_range"].is_null()) {
        auto range = config["iv_range"];
        cfg.iv_range = std::make_tuple(range[0].get<double>(), range[1].get<double>());
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

    json sf = config_json["strategy_filter"];
    
    StrategyFilter s_filter;
    s_filter.single_calls = sf["single_calls"].get<bool>();
    s_filter.iron_condors = sf["iron_condors"].get<bool>();
    s_filter.straddles = sf["straddles"].get<bool>();
    s_filter.strangles = sf["strangles"].get<bool>();

    return s_filter;
}

