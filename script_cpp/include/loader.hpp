#ifndef LOADER_HPP
#define LOADER_HPP

#include "object.hpp"
#include <string>
#include <vector>
#include <tuple>
#include <optional>
#include <stdexcept>

std::tuple<std::vector<Option>, std::optional<double>> load_option_snapshot(const std::string& path);

#endif // LOADER_HPP

