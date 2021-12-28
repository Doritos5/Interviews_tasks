import pika

queue_name = "incoming_email_files"


class Publisher(object):
    global queue_name

    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue_name, durable=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def publish_message(self, msg: bytes) -> None:
        self.channel.basic_publish(exchange="",
                                   routing_key=queue_name,
                                   body=msg,
                                   properties=pika.BasicProperties(
                                       delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                                   ))

    def close_connection(self):
        self.connection.close()


class Consumer(object):
    global queue_name

    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue_name, durable=True)

    def consume(self, callback_func: callable):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=queue_name, on_message_callback=callback_func)
        print(' [x] Waiting for messages. To exit press CTRL+C')
        self.channel.start_consuming()
