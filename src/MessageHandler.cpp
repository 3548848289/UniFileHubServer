#include "MessageHandler.h"

std::vector<std::string> MessageHandler::handle_message(char* buf, size_t len) {
    std::vector<std::string> messages;

    if (len > 0) {
        if (strncmp(buf, "chick", 5) == 0) {
            messages.push_back(handle_chick_event(buf + 5));
        } else if (strncmp(buf, "read", 4) == 0) {
            messages.push_back(handle_read_event(buf + 5));
        } else if (strncmp(buf, "clear", 5) == 0) {
            messages.push_back(handle_clear_event(buf + 5));
        }
    }

    return messages;
}

std::string MessageHandler::handle_chick_event(char* buf) {
    int row, column;
    sscanf(buf, "(%d,%d)", &row, &column);
    std::cout << "chick data: (" << row << ", " << column << ")" << std::endl;
    std::stringstream ss;
    ss << "chick (" << row << "," << column << ")\n";
    return "chick\n" + ss.str();
}

std::string MessageHandler::handle_read_event(char* buf) {
    std::string message(buf);
    std::string filename = message;
    FILE *pipe = popen(("python3 ../resouses/script.py " + filename).c_str(), "r");
    std::string result = "read\n";

    if (!pipe) {
        result += "Failed to execute Python script";
    } else {
        char buffer[1024];
        while (!feof(pipe)) {
            if (fgets(buffer, sizeof(buffer), pipe) != nullptr)
                result += buffer;
        }
        pclose(pipe);
    }
    return result;
}

std::string MessageHandler::handle_clear_event(char* buf) {
    int row, column;
    sscanf(buf, "(%d,%d)", &row, &column);
    std::cout << "clear data: (" << row << ", " << column << ")" << std::endl;
    std::stringstream ss;
    ss << "clear (" << row << "," << column << ")\n";
    return "clear\n" + ss.str();
}
