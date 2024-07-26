#include "server.h"

int main() {
    try {
        Server server(9200);
        server.start();
    } catch (std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
    }

    return 0;
}
