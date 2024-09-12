#ifndef MESSAGE_HANDLER_H
#define MESSAGE_HANDLER_H

#include <iostream>
#include <string>
#include <sstream>
#include <cstdio>
#include <vector>
#include <string>
#include <string.h>
#include <sstream>
#include <json/json.h>

class MessageHandler {
public:
    MessageHandler() {}
    std::vector<Json::Value> handle_message(char* buf, size_t len);
    std::tuple<std::string, int, int, std::string> extract_common_fields(const Json::Value& root);


private:

    Json::Value construct_json(const std::string& ip, const std::string& operation, 
                               int row, int column, const std::string& object);
    Json::Value handle_chick_event(const Json::Value& root);
    Json::Value handle_read_event(const Json::Value& root);
    Json::Value handle_clear_event(const Json::Value& root);
    Json::Value handle_edited_event(const Json::Value& root);
    
};

#endif // MESSAGE_HANDLER_H
