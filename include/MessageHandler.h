#ifndef MESSAGE_HANDLER_H
#define MESSAGE_HANDLER_H

#include <iostream>
#include <string>
#include <sstream>
#include <cstdio>
#include <vector>
#include <string.h>

class MessageHandler {
public:
    MessageHandler() {}
    std::vector<std::string> handle_message(char* buf, size_t len);

private:
    std::string handle_chick_event(char* buf);
    std::string handle_read_event(char* buf);
    std::string handle_clear_event(char* buf);
};

#endif // MESSAGE_HANDLER_H
