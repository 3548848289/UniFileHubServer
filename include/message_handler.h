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
#include "json_handler.h"


class MessageHandler {
public:
    MessageHandler() {}
    std::vector<Json::Value> handle_message(char* buf, size_t len);
    std::string execute_command(const std::string& command);

private:

    Json::Value construct_json(const std::string& ip, const std::string& operation, 
                               int row, int column, const std::string& object);
    Json::Value handle_chick_event(const Json::Value& root);
    Json::Value handle_read_event(const Json::Value& root);
    Json::Value handle_clear_event(const Json::Value& root);
    Json::Value handle_edited_event(const Json::Value& root);
    
};

#endif // MESSAGE_HANDLER_H
