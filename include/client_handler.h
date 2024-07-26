#ifndef CLIENT_HANDLER_H
#define CLIENT_HANDLER_H

#include <iostream>
#include <boost/asio.hpp>
#include <boost/algorithm/string.hpp> 


#include <vector>
#include <thread>
#include <memory>
#include <mutex>
#include "MessageHandler.h"

using boost::asio::ip::tcp;

class ClientHandler : public std::enable_shared_from_this<ClientHandler> {
public:
    ClientHandler(tcp::socket socket, std::vector<std::shared_ptr<ClientHandler>>& clients, std::mutex& mtx);

    void start();

private:
    void handle_client();
    void broadcast_message(const std::string& message);

    tcp::socket socket_;
    std::vector<std::shared_ptr<ClientHandler>>& clients_;
    std::thread thread_;
    std::mutex& mtx_;
    MessageHandler message_handler_;
    std::string sender_ip;
};

#endif // CLIENT_HANDLER_H
