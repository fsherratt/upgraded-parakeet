The rough running of this is currently:

[ UDP_SEND_MESSAGE_QUEUE ] -> UDP_Publisher (listens for messages on this) -> UDP Proxy, send message |||| UDP Proxy recieve -> UDP_Reciever (listens for messages published to udp proxy -> [ UDP_RECIEVED_MESSAGE_QUEUE ]

Currently to run the test case to implement the sending to the proxy, you can run 3 terminals.
1. python3 udp_proxy.py
-- This runs the udp proxy to listen and print messages on the standard address on local host
2. python3 udp_sender.py
-- This sets up the module to listen to rabbit mq for messages and to publish these to the standard udp proxy on local host.
3. python3 TEST_PUBLISH.py udp_message message "Test 123"
-- This is a default class that can allow you to publish messages to any rabbitmq direct type queue. The first argument is the exchange, second is the routing key and third is the message.
