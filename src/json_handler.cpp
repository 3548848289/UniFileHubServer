#include "json_handler.h"
#include <iostream>

bool JsonHandler::parse_json(const std::string& data, Json::Value& root) {
    Json::Reader reader;
    return reader.parse(data, root);
}

Json::Value JsonHandler::construct_json(const std::string& ip, const std::string& operation, 
                                        int row, int column, const std::string& object) {
    Json::Value json;
    json["ip"] = ip;
    json["operation"] = operation;
    json["row"] = row;
    json["column"] = column;
    json["object"] = object;
    return json;
}

Json::Value JsonHandler::construct_error(const std::string& error_message) {
    Json::Value json;
    json["error"] = error_message;
    return json;
}

std::tuple<std::string, int, int, std::string> JsonHandler::extract_common_fields(const Json::Value& root) {
    std::string ip = get_string_field(root, "ip");
    int row = get_int_field(root, "row");
    int column = get_int_field(root, "column");
    std::string object = get_string_field(root, "object");
    return {ip, row, column, object};
}

std::string JsonHandler::get_string_field(const Json::Value& root, const std::string& key) {
    return root.isMember(key) ? root[key].asString() : "";
}

int JsonHandler::get_int_field(const Json::Value& root, const std::string& key) {
    return root.isMember(key) ? root[key].asInt() : 0;
}
