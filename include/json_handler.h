#pragma once
#include <json/json.h>
#include <string>

class JsonHandler {
public:
    // 解析字符串为 JSON
    static bool parse_json(const std::string& data, Json::Value& root);

    // 构造标准响应
    static Json::Value construct_json(const std::string& ip, const std::string& operation, 
                                      int row, int column, const std::string& object);

    // 构造错误消息
    static Json::Value construct_error(const std::string& error_message);

    // 提取公共字段
    static std::tuple<std::string, int, int, std::string> extract_common_fields(const Json::Value& root);

private:
    // Helper 函数，确保字段存在并且有效
    static std::string get_string_field(const Json::Value& root, const std::string& key);
    static int get_int_field(const Json::Value& root, const std::string& key);
};
