# Rabbit MQ instruction set
>RabbitMQ is the most widely deployed open source message broker.
Rabbit MQ is a message broker. This means it listens for incoming data on a set of "exchanges" and publish the data recieved to these to any valid subscribers. This follows the standard software publish-subscriber pattern.

## Installation
To install from the package cloud:

* First import PackageCloud signing key
	* wget -O - "https://packagecloud.io/rabbitmq/rabbitmq-server/gpgkey" | sudo apt-key add -
* Then run the install script
	* curl -s https://packagecloud.io/install/repositories/rabbitmq/rabbitmq-server/script.deb.sh | sudo bash
* Then install rabbit mq server
	* sudo apt-get update && sudo apt-get install rabbitmq-server -y --fix-missing

## How to use queues
### Queues in use
The current design assumes a simple routing model. We designate queues for individaul data streams and publish to them when we want to distribute data. The current list of queues is:
* udp_message
	* recieved (for passing on recieved messages on the recieving proxy)
	* message (for sending messages to a publisher proxy)

### Publishing and subscribing
#### Setup queue
To setup to publish or subscribe you first need to declare the queue, as shown below.
```python3
from udp_proxy import udp_proxy
import pika

connection = pika.BlockingConnection(
            pika.ConnectionParameters( host = 'localhost' ) )
channel = connection.channel()
channel.exchange_declare( exchange='exhange_name_here', exchange_type='direct' )
```
Re-declaring an exchange doesn't matter. You MUST make sure it is declared before using it.

#### Publish
To publish to a queue, you must just declare the  the exchange and routing key to be published in the publish function. This is done by:
```python3
channel.basic_publish(
                exchange='exchange_name_here',
                routing_key='routing_key_here',
                body=item_to_be_sent_here )
```
This will simply send the data set in the body to the exchange. Any subscribers listening on the routing key of this exchange will recieve the data.

#### Subscribe
To subscribe, you must setup a queue to listen on, then bind that to the relevant exchange. This is done by
```python3
result = channel.queue_declare( queue='', exclusive=True )
queue_name = result.method.queue

channel.queue_bind( exchange="exchange_name_here", queue=queue_name, routing_key="routing_key_here" )
```

To listen for data, you must declare a consuming  method. This involves declaring the queue to be listened to and the callback to be used. I belive you can declare multiple queues on a channel and start processing them dependant on which one recieves data. The consume is done as follows:
```python3
channel.basic_consume(
            queue=queue_name, on_message_callback=function_to_run, auto_ack=True )
channel.start_consuming()
```

### Tutoirals and improvements
[Rabbit MQ tutorial on Routing|https://www.rabbitmq.com/tutorials/tutorial-four-python.html]
As an improvement, it might be worth converting them to topics as shown [here|https://www.rabbitmq.com/tutorials/tutorial-five-python.html], however this is currently assumed to be good enough.
