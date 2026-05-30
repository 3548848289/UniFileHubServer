#include "message_handler.h"
#ifdef _WIN32
#define popen _popen
#define pclose _pclose
#endif

std::string MessageHandler::execute_command(const std::string& command) {
    FILE* pipe = popen(command.c_str(), "r");
    if (!pipe) return "Failed to execute command";

    char buffer[8192];
    std::string result;
    while (!feof(pipe)) {
        if (fgets(buffer, sizeof(buffer), pipe) != nullptr)
            result += buffer;
    }
    pclose(pipe);
    return result;
}

std::vector<Json::Value> MessageHandler::handle_message(const char* buf, size_t len) {
    std::vector<Json::Value> messages;
    if (len > 0) {
        Json::Value root;
        if (!JsonHandler::parse_json(std::string(buf, len), root)) {
            return { JsonHandler::construct_error("Invalid JSON format") };
        }

        auto operation = root["operation"].asString();
        if (operation == "chick") {
            messages.push_back(handle_chick_event(root));
        } else if (operation == "read") {
            messages.push_back(handle_read_event(root));
        } else if (operation == "clear") {
            messages.push_back(handle_clear_event(root));
        } else if (operation == "edited") {
            messages.push_back(handle_edited_event(root));
        } else if (operation == "disconnect") {  
            messages.push_back(handle_disconnect_event(root));
        } else {
            messages.push_back(JsonHandler::construct_error("Unknown operation"));
        }
    }
    return messages;
}


Json::Value MessageHandler::handle_read_event(const Json::Value& root) {
    auto [ip, row, column, filename] = JsonHandler::extract_common_fields(root);
    std::cout << "filename" << filename << std::endl;
    std::string result = execute_command("python.exe ../../scripts/read_csv.py " + filename);
    return JsonHandler::construct_json(ip, "read", row, column, result);
}

Json::Value MessageHandler::handle_chick_event(const Json::Value& root) {
    auto [ip, row, column, object] = JsonHandler::extract_common_fields(root);
    return JsonHandler::construct_json(ip, "chick", row, column, "");
}

Json::Value MessageHandler::handle_clear_event(const Json::Value& root) {
    auto [ip, row, column, object] = JsonHandler::extract_common_fields(root);
    return JsonHandler::construct_json(ip, "clear", row, column, "");
}

Json::Value MessageHandler::handle_edited_event(const Json::Value& root) {
    auto [ip, row, column, text] = JsonHandler::extract_common_fields(root);
    execute_command("python.exe scripts/update_csv.py class1.csv " + 
                    std::to_string(row) + " " + std::to_string(column) + " " + text);
    return JsonHandler::construct_json(ip, "edited", row, column, text);
}

Json::Value MessageHandler::handle_disconnect_event(const Json::Value& root) {
    // Json::Value msg;
    // msg["type"] = "system";
    // msg["event"] = "disconnect";
    // msg["ip"] = root["ip"];  // 来自 JsonHandler::construct_system_message
    // msg["message"] = root.get("message", "Client disconnected");
    // return msg;
    auto [ip, row, column, object] = JsonHandler::extract_common_fields(root);
    return JsonHandler::construct_json(ip, "disconnect", row, column, "");
}