#include "loader.hpp"
#include <fstream>
#include <iostream>
#include <sstream>
#include <json.hpp>
#include <chrono>
#include <iomanip>
#include <ctime>
#include <cmath>

using json = nlohmann::json;

static double mid_price(const json& opt) {
    auto bid = opt.find("bid");
    auto ask = opt.find("ask");
    auto last = opt.find("last");

    if (bid != opt.end() && ask != opt.end() && 
        bid->is_number() && ask->is_number()) {
        return (bid->get<double>() + ask->get<double>()) / 2.0;
    }
    if (last != opt.end() && last->is_number()) {
        return last->get<double>();
    }
    return 0.0;
}

static std::optional<double> extract_iv(const json& greeks) {
    if (greeks.is_null() || !greeks.is_object()) {
        return std::nullopt;
    }

    std::vector<std::string> iv_keys = {
        "mid_iv", "bid_iv", "ask_iv", "smv_vol", 
        "implied_volatility", "volatility"
    };

    for (const auto& key : iv_keys) {
        auto it = greeks.find(key);
        if (it != greeks.end() && it->is_number()) {
            double val = it->get<double>();
            if (val > 0) {
                return val;
            }
        }
    }
    return std::nullopt;
}

static int calculate_days_to_expiry(const std::string& expiry_str) {
    std::tm tm = {};
    std::istringstream ss(expiry_str);
    ss >> std::get_time(&tm, "%Y-%m-%d");
    
    auto expiry_time = std::mktime(&tm);
    auto now = std::chrono::system_clock::now();
    auto now_time = std::chrono::system_clock::to_time_t(now);
    
    double diff_seconds = std::difftime(expiry_time, now_time);
    return static_cast<int>(std::floor(diff_seconds / 86400.0));
}

std::tuple<std::vector<Option>, std::optional<double>> load_option_snapshot(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open file: " + path);
    }

    json data;
    file >> data;

    std::string symbol = data["symbols"][0].get<std::string>();
    auto chains = data["chains"][symbol];
    auto underlying = data.value("underlying", json::object());

    // Get spot price
    std::optional<double> spot;
    auto bid = underlying.find("bid");
    auto ask = underlying.find("ask");
    auto last = underlying.find("last");

    if (bid != underlying.end() && ask != underlying.end() &&
        bid->is_number() && ask->is_number()) {
        spot = (bid->get<double>() + ask->get<double>()) / 2.0;
    } else if (last != underlying.end() && last->is_number()) {
        spot = last->get<double>();
    }

    // Convert chain rows into Option objects
    std::vector<Option> options;
    for (auto& [expiry_key, rows] : chains.items()) {
        for (auto& opt_data : rows) {
            std::string side = opt_data["option_type"].get<std::string>();
            std::transform(side.begin(), side.end(), side.begin(), ::toupper);
            side = (side == "CALL") ? "CALL" : "PUT";

            auto greeks = opt_data.value("greeks", json::object());
            std::string expiry_str = opt_data["expiration_date"].get<std::string>();
            int days_to_expiry = calculate_days_to_expiry(expiry_str);

            std::optional<double> bid_val, ask_val;
            if (opt_data.contains("bid") && opt_data["bid"].is_number()) {
                bid_val = opt_data["bid"].get<double>();
            }
            if (opt_data.contains("ask") && opt_data["ask"].is_number()) {
                ask_val = opt_data["ask"].get<double>();
            }

            Option opt;
            opt.symbol = symbol;
            opt.expiry = expiry_str;
            opt.strike = opt_data["strike"].get<double>();
            opt.side = side;
            opt.mid = mid_price(opt_data);
            opt.iv = extract_iv(greeks).value_or(0.0);
            opt.volume = opt_data.value("volume", 0.0);
            opt.oi = opt_data.value("open_interest", 0.0);
            opt.bid = bid_val;
            opt.ask = ask_val;
            opt.delta = greeks.value("delta", 0.0);
            opt.gamma = greeks.value("gamma", 0.0);
            opt.theta = greeks.value("theta", 0.0);
            opt.vega = greeks.value("vega", 0.0);
            opt.rho = greeks.value("rho", 0.0);
            opt.days_to_expiry = days_to_expiry;

            options.push_back(opt);
        }
    }

    return {options, spot};
}

