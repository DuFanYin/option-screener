#include "loader.hpp"
#include "factory/factory.hpp"
#include "config.hpp"
#include <iostream>
#include <fstream>
#include <filesystem>
#include <vector>
#include <json.hpp>

using json = nlohmann::json;

int main(int argc, char* argv[]) {
    try {
        // Get config file path (default: config.json)
        std::string config_path = "config.json";
        std::string data_path;
        
        if (argc > 1) {
            config_path = argv[1];
        }
        if (argc > 2) {
            data_path = argv[2];
        }

        // Check if config file exists
        if (!std::filesystem::exists(config_path)) {
            std::cerr << "Error: Config file not found: " << config_path << std::endl;
            std::cerr << "Usage: " << (argc > 0 ? argv[0] : "option_screener") << " [config.json] [data_file]" << std::endl;
            return 1;
        }

        // Check if data file exists
        if (data_path.empty() || !std::filesystem::exists(data_path)) {
            std::cerr << "Error: Data file not found: " << (data_path.empty() ? "(not provided)" : data_path) << std::endl;
            std::cerr << "Usage: " << (argc > 0 ? argv[0] : "option_screener") << " [config.json] [data_file]" << std::endl;
            return 1;
        }

        // Load filters from config
        StrategyFilter s_filter = ConfigLoader::load_strategy_filter_from_json(config_path);
        ConfigFilter c_filter = ConfigLoader::load_from_json(config_path);
        
        // Load config JSON for ranking settings
        json config_json;
        {
            std::ifstream config_file(config_path);
            config_json = json::parse(config_file);
        }

        // Load options and spot
        auto [options, spot] = load_option_snapshot(data_path);
        
        if (!spot.has_value()) {
            std::cerr << "Error: Could not determine spot price" << std::endl;
            return 1;
        }

        // Create factory and generate strategies
        StrategyFactory factory(options, spot.value());
        
        // Get ranking parameters from config
        auto ranking = config_json["ranking"];
        std::string rank_key = ranking["key"].get<std::string>();
        size_t top_n = ranking["top_n"].get<size_t>();

        // Generate, rank, and get top strategies
        auto results = factory.strategy(s_filter, c_filter).rank(rank_key).top(top_n);

        std::cout << "Found " << results.size() << " strategies" << std::endl;
        std::cout << "Ranked by: " << rank_key << std::endl;
        std::cout << "----------------------------------------" << std::endl;
        results.print();

        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}
