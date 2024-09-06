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
        }else if (strncmp(buf, "edited", 6) == 0) {
            messages.push_back(handle_edited_event(buf));
        }
    }
    
    return messages;
}

std::string MessageHandler::handle_chick_event(char* buf) {
    int row, column;
    sscanf(buf, "(%d,%d)", &row, &column);      
    // std::cout << "chick data: (" << row << ", " << column << ")" << std::endl;
    std::stringstream ss;
    ss << "chick (" << row << "," << column << ")\n";
    return "chick\n" + ss.str();
}

std::string MessageHandler::handle_read_event(char* buf) {
    std::string message(buf);
    std::string filename = message;
    FILE *pipe = popen(("python3 ../resources/script.py " + filename).c_str(), "r");
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

std::string MessageHandler::handle_clear_event(char* buf    ) {
    int row, column;
    sscanf(buf, "(%d,%d)", &row, &column);
    // std::cout << "clear data: (" << row << ", " << column << ")" << std::endl;
    std::stringstream ss;
    ss << "clear (" << row << "," << column << ")\n";
    return "clear\n" + ss.str();
}



std::vector<std::string> split(const std::string &s, char delimiter) {
    std::vector<std::string> tokens;
    std::string token;
    std::istringstream tokenStream(s);
    while (std::getline(tokenStream, token, delimiter)) {
        tokens.push_back(token);
    }
    return tokens;
}


std::string MessageHandler::handle_edited_event(std::string buf) {
    // std::cout << "buf is " << buf << std::endl;
    std::vector<std::string> parts = split(buf, ',');

    if (parts.size() != 5) 
        return "Invalid data format";

    std::string action = parts[0];   
    int row = std::stoi(parts[1]);   
    int col = std::stoi(parts[2]); 
    int length = std::stoi(parts[3]); 
    std::string text = parts[4];     
    std::cout << "Action: " << action << ", Row: " << row << ", Column: " << col
              << ", Length: " << length << ", Text: " << text << std::endl;

    std::string command = "python3 ../resources/update_csv.py ../resources/class1.csv ";    // 构造Python脚本调用命令
    command += std::to_string(row) + " ";
    command += std::to_string(col) + " ";
    command += text;
    
    std::cout << command << std::endl;
    int result = std::system(command.c_str());
    
    std::stringstream ss;
    ss << "edited(" << row << "," << col << "," << text;
    return "edited\n" + ss.str();
        
}
