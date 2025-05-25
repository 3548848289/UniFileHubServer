#include "server.h"

int main() {
    try {
        std::cout << "SharedCSV:5003 is starting" << std::endl;
        Server server(5003);
        server.start();
    } catch (std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
    }

    return 0;
}
