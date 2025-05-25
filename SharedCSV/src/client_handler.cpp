#include "client_handler.h"
namespace fs = std::filesystem;


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

            sender_ip = socket_.remote_endpoint().address().to_string();
            std::vector<Json::Value> messages = message_handler_.handle_message(buf, len);
            for (const auto& message : messages) {
                std::cout << message << std::endl;
                broadcast_message(message);
            }
        }
    } catch (const boost::system::system_error& e) {
        if (e.code() == boost::asio::error::eof) {
            std::cout << "客户端断开连接。" << std::endl;
            // clear_file();
        }
        else 
            std::cerr << "handle_client 异常: " << e.what() << std::endl;
        
        Json::Value disconnect = JsonHandler::construct_system_message(
            sender_ip, "disconnect", "Client disconnected");
            
        std::string disconnect_str = Json::writeString(Json::StreamWriterBuilder(), disconnect);
        std::vector<Json::Value> messages = message_handler_.handle_message(
            disconnect_str.data(), disconnect_str.size());
        
        for (const auto& msg : messages) 
            broadcast_message(msg);
        // 无论哪种异常都清理 client
        std::lock_guard<std::mutex> lock(mtx_);
        clients_.erase(std::remove(clients_.begin(), clients_.end(), shared_from_this()), clients_.end());
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



void ClientHandler::clear_file() {
    const std::string folder = "../resources";
    try {
        for (const auto& entry : fs::directory_iterator(folder)) {
            fs::remove_all(entry);  // 删除文件或目录
        }
        std::cout << "已清空 resources 文件夹" << std::endl;
    } catch (const std::exception& ex) {
        std::cerr << "清空 resources 文件夹时出错: " << ex.what() << std::endl;
    }
}