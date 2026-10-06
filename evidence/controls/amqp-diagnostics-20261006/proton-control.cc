// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <proton/connection.hpp>
#include <proton/container.hpp>
#include <proton/delivery.hpp>
#include <proton/message.hpp>
#include <proton/messaging_handler.hpp>
#include <proton/receiver.hpp>
#include <proton/receiver_options.hpp>
#include <proton/sender.hpp>
#include <proton/error_condition.hpp>
#include <iostream>
#include <stdexcept>
#include <string>
class Control final : public proton::messaging_handler {
 public:
  explicit Control(bool closing, unsigned iteration) : closing_(closing), address_("native-control-"+std::to_string(iteration)) {}
  void on_container_start(proton::container& c) override { c.connect("amqp://guest:guest@amqp-broker:5672"); }
  void on_connection_open(proton::connection& c) override {
    connection_=c;
    c.open_receiver(address_,proton::receiver_options().auto_accept(false));
    if (closing_) { ++checks_; c.close(); }
    else { c.open_sender(address_); }
  }
  void on_sendable(proton::sender& sender) override {
    if (!sent_) { sent_=true; sender.send(proton::message(std::string("deliberately rejected"))); }
  }
  void on_message(proton::delivery& delivery,proton::message& message) override {
    if (proton::get<std::string>(message.body())!="deliberately rejected") { throw std::runtime_error("incorrect body"); }
    delivery.reject(); ++checks_; connection_.close();
  }
  void on_error(const proton::error_condition& e) override {
    if (closing_ && e.name()=="amqp:internal-error" && e.description()=="Unrecoverable error: AMQ119027: Invalid AMQPConnection Remote State: CLOSED") {
      std::cout<<"Expected broker close-race diagnostic: "<<e.what()<<'\n';
      return;
    }
    throw std::runtime_error(e.what());
  }
  unsigned checks() const { return checks_; }
 private:
  bool closing_,sent_=false;
  std::string address_;
  proton::connection connection_;
  unsigned checks_=0;
};
int main(int argc,char** argv) {
  try {
    if (argc!=2 || (std::string(argv[1])!="close" && std::string(argv[1])!="reject")) { return 2; }
    bool close=std::string(argv[1])=="close";
    for (unsigned i=0;i<20;++i) { Control handler(close,i); proton::container(handler).run(); if (handler.checks()!=1) { return 3; } }
    std::cout<<"20 standalone Proton "<<argv[1]<<" controls passed\n";
  } catch (const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
