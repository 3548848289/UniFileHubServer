#include "server.h"

Server::Server(short port) : acceptor_(io_context_, tcp::endpoint(tcp::v4(), port)) {}

void Server::start() {
    accept_connections();
    io_context_.run();
}

void Server::accept_connections() {
    acceptor_.async_accept(
        [this](std::error_code ec, tcp::socket socket) {
            if (!ec) {
                std::cout << "New connection from: " << socket.remote_endpoint().address().to_string() << std::endl;
                auto handler = std::make_shared<ClientHandler>(std::move(socket), clients_, mtx_);
                handler->start();
            }
            accept_connections();
        });
}
