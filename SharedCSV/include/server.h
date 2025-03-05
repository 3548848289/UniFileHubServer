#ifndef SERVER_H
#define SERVER_H

#include <iostream>
#include <boost/asio.hpp>
#include <vector>
#include <memory>
#include <mutex>
#include "client_handler.h"

using boost::asio::ip::tcp;

class Server {
public:
    Server(short port);
    void start();

private:
    void accept_connections();

    boost::asio::io_context io_context_;
    tcp::acceptor acceptor_;
    std::vector<std::shared_ptr<ClientHandler>> clients_;
    std::mutex mtx_;
};

#endif // SERVER_H
