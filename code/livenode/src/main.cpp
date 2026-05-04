#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <map>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <json.hpp>
#include "orders.cpp" // Simple inclusion for this minimal project

using json = nlohmann::json;

std::map<std::string, std::string> load_config() {
    std::map<std::string, std::string> config;
    std::ifstream file("api.txt");
    std::string line;
    while (std::getline(file, line)) {
        size_t colon = line.find(':');
        if (colon != std::string::npos) {
            std::string key = line.substr(0, colon);
            std::string value = line.substr(colon + 1);
            // Trim whitespace
            key.erase(0, key.find_first_not_of(" \t"));
            key.erase(key.find_last_not_of(" \t") + 1);
            value.erase(0, value.find_first_not_of(" \t"));
            value.erase(value.find_last_not_of(" \t") + 1);
            config[key] = value;
        }
    }
    return config;
}

int main() {
    auto config = load_config();
    if (config.find("API") == config.end() || config.find("SECRET") == config.end() || config.find("ENDPOINT") == config.end()) {
        std::cerr << "Error: Missing API, SECRET, or ENDPOINT in api.txt" << std::endl;
        return 1;
    }

    AlpacaExecutor executor(config["API"], config["SECRET"], config["ENDPOINT"]);

    int server_fd, new_socket;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);
    char buffer[1024] = {0};

    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt))) {
        perror("setsockopt");
        exit(EXIT_FAILURE);
    }

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(5555);

    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }

    if (listen(server_fd, 3) < 0) {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    std::cout << "Livenode C++ Execution Engine listening on port 5555..." << std::endl;

    while (true) {
        if ((new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
            perror("accept");
            continue;
        }

        read(new_socket, buffer, 1024);
        std::string request(buffer);
        std::cout << "Received Signal: " << request << std::endl;

        try {
            auto signal = json::parse(request);
            std::string symbol = signal["symbol"];
            int qty = signal["qty"];
            std::string side = signal["side"];
            std::string type = signal["type"];

            std::cout << "Executing " << side << " " << qty << " shares of " << symbol << "..." << std::endl;
            
            bool success = executor.place_order(symbol, qty, side, type);
            
            std::string response = success ? "{\"status\": \"success\"}" : "{\"status\": \"error\"}";
            send(new_socket, response.c_str(), response.length(), 0);
        } catch (std::exception& e) {
            std::cerr << "Error parsing JSON: " << e.what() << std::endl;
            std::string response = "{\"status\": \"parse_error\"}";
            send(new_socket, response.c_str(), response.length(), 0);
        }

        close(new_socket);
        memset(buffer, 0, 1024);
    }

    return 0;
}
