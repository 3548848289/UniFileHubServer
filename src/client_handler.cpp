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
            char buf[1024];
            size_t len = socket_.receive(boost::asio::buffer(buf, sizeof(buf)));

            if (len > 0) {
                std::vector<std::string> messages = message_handler_.handle_message(buf, len);
                for (const auto& message : messages) {
                    broadcast_message(message);
                }
            }
        }
    } catch (std::exception& e) {
        std::cerr << "Exception in thread: " << e.what() << std::endl;
    }
}

void ClientHandler::broadcast_message(const std::string& message) {
    std::lock_guard<std::mutex> lock(mtx_);
    for (auto& client : clients_) {
        boost::asio::write(client->socket_, boost::asio::buffer(message));
    }
}
