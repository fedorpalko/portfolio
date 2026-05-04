#include <iostream>
#include <string>
#include <curl/curl.h>
#include <json.hpp>

using json = nlohmann::json;

class AlpacaExecutor {
private:
    std::string api_key;
    std::string secret_key;
    std::string endpoint;

    static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
        ((std::string*)userp)->append((char*)contents, size * nmemb);
        return size * nmemb;
    }

public:
    AlpacaExecutor(std::string key, std::string secret, std::string url) 
        : api_key(key), secret_key(secret), endpoint(url) {}

    bool place_order(const std::string& symbol, int qty, const std::string& side, const std::string& type) {
        CURL* curl;
        CURLcode res;
        std::string readBuffer;

        curl = curl_easy_init();
        if (curl) {
            std::string url = endpoint + "/orders";
            
            json payload = {
                {"symbol", symbol},
                {"qty", std::to_string(qty)},
                {"side", side},
                {"type", type},
                {"time_in_force", "gtc"}
            };

            std::string json_str = payload.dump();

            struct curl_slist* headers = NULL;
            headers = curl_slist_append(headers, "Content-Type: application/json");
            headers = curl_slist_append(headers, ("APCA-API-KEY-ID: " + api_key).c_str());
            headers = curl_slist_append(headers, ("APCA-API-SECRET-KEY: " + secret_key).c_str());

            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_str.c_str());
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

            res = curl_easy_perform(curl);
            
            if (res != CURLE_OK) {
                std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
                return false;
            } else {
                long response_code;
                curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
                std::cout << "Alpaca Response Code: " << response_code << std::endl;
                std::cout << "Response: " << readBuffer << std::endl;
                
                if (response_code >= 200 && response_code < 300) {
                    return true;
                }
            }

            curl_easy_cleanup(curl);
        }
        return false;
    }
};
