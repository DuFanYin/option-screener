#include "loader.hpp"
#include "factory/factory.hpp"
#include <iostream>

#include <filesystem>
#include <cstdlib>

int main() {
    try {
        // Get path relative to executable or current directory
        std::string data_path = "data/pltr.json";
        std::filesystem::path exe_path = std::filesystem::current_path();
        
        // Try multiple possible paths
        std::vector<std::filesystem::path> possible_paths = {
            data_path,
            exe_path / "data" / "pltr.json",
            exe_path.parent_path().parent_path() / "data" / "pltr.json",
            std::filesystem::path("../data/pltr.json"),
        };
        
        std::string final_path;
        bool found = false;
        for (const auto& path : possible_paths) {
            if (std::filesystem::exists(path)) {
                final_path = path.string();
                found = true;
                break;
            }
        }
        
        if (!found) {
            std::cerr << "Error: Cannot find data/pltr.json in any of these locations:" << std::endl;
            for (const auto& path : possible_paths) {
                std::cerr << "  - " << path.string() << std::endl;
            }
            return 1;
        }
        
        auto [options, spot] = load_option_snapshot(final_path);
        
        if (!spot.has_value()) {
            std::cerr << "Error: Could not determine spot price" << std::endl;
            return 1;
        }

        StrategyFactory factory(options, spot.value());

        StrategyFilter s_filter;
        s_filter.straddles = true;

        ConfigFilter c_filter;
        c_filter.min_oi = 5;
        c_filter.min_price = 0.05;
        c_filter.days_to_expiry_range = std::make_tuple(0, 30);
        c_filter.direction = Direction::SHORT;
        c_filter.credit_range = std::make_tuple(0.0, 2500.0);

        auto results = factory.strategy(s_filter, c_filter).rank("cost").top(10);

        std::cout << "Found " << results.size() << " strategies" << std::endl;
        results.print();

        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}

