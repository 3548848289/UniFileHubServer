#include "client_handler.h"

ClientHandler::ClientHandler(tcp::socket socket, std::vector<std::shared_ptr<ClientHandler>>& clients, std::mutex& mtx)
    : socket_(std::move(socket)), clients_(clients), mtx_(mtx) {}

void ClientHandler::start() {
    thread_ = std::thread(&ClientHandler::handle_client, shared_from_this());
    thread_.detach();
}

void ClientHandler::handle_client() {
    try {
        {
            std::lock_guard<std::mutex> lock(mtx_);
            clients_.push_back(shared_from_this());
        }
        while (true) {
            char buf[8192] = {0};
            size_t len = socket_.receive(boost::asio::buffer(buf, sizeof(buf)));

            if (len > 0) {
                sender_ip = socket_.remote_endpoint().address().to_string();
                std::vector<Json::Value> messages = message_handler_.handle_message(buf, len);
                for (const auto& message : messages) {
                    std::cout << message << std::endl;

                    broadcast_message(message);
                }
            } else {
                std::lock_guard<std::mutex> lock(mtx_);
                clients_.erase(std::remove(clients_.begin(), clients_.end(), shared_from_this()), clients_.end());
                break; 
            }
        }
    } catch (std::exception& e) {
        std::cerr << "handle_client Exception in thread: " << e.what() << std::endl;
    }
}

void ClientHandler::broadcast_message(const Json::Value& message) {
    if (!message.isObject()) {
        std::cerr << "Invalid JSON format: Not an object" << std::endl;
        return;
    }
    std::lock_guard<std::mutex> lock(mtx_);
    for (auto it = clients_.begin(); it != clients_.end(); ) {
        try {
            Json::StreamWriterBuilder writer;
            std::string message_str = Json::writeString(writer, message);
            boost::asio::write((*it)->socket_, boost::asio::buffer(message_str));
            ++it;
        } catch (boost::system::system_error& e) {
            std::cerr << "broadcast_message Exception in thread: write: " << e.what() << std::endl;
            it = clients_.erase(it); 
        }
    }
}

