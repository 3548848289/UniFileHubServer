#include "MessageHandler.h"
#include <json/json.h>
#include <sstream>
#include <iostream>

std::vector<Json::Value> MessageHandler::handle_message(char* buf, size_t len) {
    std::vector<Json::Value> messages;    
    if (len > 0) {
        Json::Value root;
        Json::Reader reader;
        
        // 解析 JSON 数据
        if (!reader.parse(buf, root)) {
            Json::Value error;
            error["error"] = "Invalid JSON format";
            messages.push_back(error);
            return messages;
        }

        std::string operation = root["operation"].asString();  
        if (operation == "chick") {
            std::cout << "chick" << std::endl;
            messages.push_back(handle_chick_event(root));
        } else if (operation == "read") {
            messages.push_back(handle_read_event(root));
        } else if (operation == "clear") {
            messages.push_back(handle_clear_event(root));
        } else if (operation == "edited") {
            messages.push_back(handle_edited_event(root));
        } else {
            Json::Value unknownOp;
            unknownOp["error"] = "Unknown operation";
            messages.push_back(unknownOp);
        }
    }
    
    return messages;
}

Json::Value MessageHandler::construct_json(const std::string& ip, const std::string& operation, 
                           int row, int column, const std::string& object) {
    Json::Value json;
    json["ip"] = ip;
    json["operation"] = operation;
    json["row"] = row;
    json["column"] = column;
    json["object"] = object;
    
    return json;
}

Json::Value MessageHandler::handle_chick_event(const Json::Value& root) {
    std::string ip = root["ip"].asString();
    int row = root["row"].asInt();
    int column = root["column"].asInt();
    std::cout << ip << "chick:" << row << column <<  std::endl;

    Json::Value response = construct_json(ip,"chick", row, column, "");
    return response;
}

Json::Value MessageHandler::handle_read_event(const Json::Value& root) {

    std::string ip = root["ip"].asString();
    std::string filename = root["object"].asString();  

    FILE *pipe = popen(("python3 ../resources/script.py " + filename).c_str(), "r");   
    Json::Value response;

    if (!pipe) {
        response["error"] = "Failed to execute Python script";
    } else {
        char buffer[1024];
        std::string result;
        while (!feof(pipe)) {
            if (fgets(buffer, sizeof(buffer), pipe) != nullptr)
                result += buffer;
        }
        pclose(pipe);
        response = construct_json(ip,"read", 0, 0, result);

    }
    return response;
}

Json::Value MessageHandler::handle_clear_event(const Json::Value& root) {
    std::string ip = root["ip"].asString();
    int row = root["row"].asInt();
    int column = root["column"].asInt();
    Json::Value response = construct_json(ip,"clear", row, column, "");
    return response;
}

Json::Value MessageHandler::handle_edited_event(const Json::Value& root) {
    std::string ip = root["ip"].asString();
    int row = root["row"].asInt();
    int col = root["column"].asInt();
    std::string text = root["object"].asString();  


    std::string command = "python3 ../resources/update_csv.py ../resources/class1.csv ";
    command += std::to_string(row) + " ";
    command += std::to_string(col) + " ";
    command += text;

    std::cout << command << std::endl;
    int result = std::system(command.c_str());
    Json::Value response = construct_json(ip,"edited", row, col, text);
    return response;
}
