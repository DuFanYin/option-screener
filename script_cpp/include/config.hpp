#ifndef CONFIG_HPP
#define CONFIG_HPP

#include "object.hpp"
#include <string>
#include <optional>

class ConfigLoader {
public:
    static ConfigFilter load_from_json(const std::string& path);
    static StrategyFilter load_strategy_filter_from_json(const std::string& path);
};

#endif // CONFIG_HPP

