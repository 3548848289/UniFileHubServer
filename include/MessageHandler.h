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

class MessageHandler {
public:
    MessageHandler() {}
    std::vector<std::string> handle_message(char* buf, size_t len);

private:
    std::string handle_chick_event(char* buf);
    std::string handle_read_event(char* buf);
    std::string handle_clear_event(char* buf);
    std::string handle_edited_event(std::string buf);
    
};

#endif // MESSAGE_HANDLER_H
