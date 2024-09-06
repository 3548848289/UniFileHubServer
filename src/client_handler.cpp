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
            char buf[1024] = {0};
            size_t len = socket_.receive(boost::asio::buffer(buf, sizeof(buf)));

            if (len > 0) {
                sender_ip = socket_.remote_endpoint().address().to_string();
                std::vector<std::string> messages = message_handler_.handle_message(buf, len);
                for (const auto& message : messages) {
                    broadcast_message(message);
                }
            } else {
                std::lock_guard<std::mutex> lock(mtx_);
                clients_.erase(std::remove(clients_.begin(), clients_.end(), shared_from_this()), clients_.end());
                break; 
            }
        }
    } catch (std::exception& e) {
        std::cerr << "Exception in thread: " << e.what() << std::endl;
    }
}

void ClientHandler::broadcast_message(const std::string& message) {
    std::lock_guard<std::mutex> lock(mtx_);
    for (auto it = clients_.begin(); it != clients_.end(); ) {
        try {
            
            std::vector<std::string> lines;
            boost::split(lines, message, boost::is_any_of("\n"));

            std::string message_with_ip = message;
            if (!lines.empty() && lines[0] != "read") {
                // 确保 lines 至少有两行
                if (lines.size() >= 2) {
                    message_with_ip = lines[0] + "\n" + sender_ip + "\n" + lines[1];
                    std::cout << " messege:" << message_with_ip << std::endl;

                } else {
                    message_with_ip = lines[0] + "\n" + sender_ip;                    // 处理 lines 只有一行或不足两行的情况
                }
            }

            // 发送消息给客户端
            boost::asio::write((*it)->socket_, boost::asio::buffer(message_with_ip));
            ++it;
        } catch (boost::system::system_error& e) {
            std::cerr << "Exception in thread: write: " << e.what() << std::endl;
            it = clients_.erase(it); 
        }
    }
}

