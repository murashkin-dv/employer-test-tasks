import argparse
from base64 import decode

from confluent_kafka import Consumer, KafkaError, Producer


def produce_message(topic, message, kafka_instance) -> None:
    """
    Function produces messages from client
    :param topic: topic name
    :param message: message text
    :param kafka_instance: kafka cluster
    :return: none
    """
    producer = Producer({'bootstrap.servers': kafka_instance})

    if type(topic) == bytes:
        topic = topic.decode('utf-8')
    if type(message) == bytes:
        message = message.decode('utf-8')

    def delivery_report(err, msg) -> None:
        """
        Callback function that will be called for each message sent to the Kafka cluster
        :param err: error message
        :param msg: message text
        :return: none
        """
        if err is not None:
            print('Message delivery failed: {}'.format(err))
        else:
            print('Message delivered to {}'.format(msg.topic()))

    producer.produce(topic, message, callback=delivery_report)
    producer.flush()


def consume_messages(topic, kafka_instance):
    """
    Function consumes and prints messages
    :param topic: topic name
    :param kafka_instance: kafka cluster
    :return:
    """
    consumer = Consumer({
        'bootstrap.servers': kafka_instance,
        'group.id'         : 'my-group',
        'auto.offset.reset': 'earliest',
    }
    )

    consumer.subscribe([topic])

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:  # ignore
                    print('End of partition event')
                else:
                    print('Error while consuming message: {}'.format(msg.error()))
            else:
                print(
                        'Consumed message: {} from topic {}'.format(
                                msg.value().decode('utf-8'),
                                msg.topic(),
                        )
                )
    except KeyboardInterrupt:
        consumer.close()


def main() -> None:
    """
    Main function reads arguments from command line
    :return:none
    """
    parser = argparse.ArgumentParser(description="Kafka producer/consumer tool")
    parser.add_argument("--mode", choices=["produce", "consume"])
    parser.add_argument("--message", help="Message to produce (for produce mode)")
    parser.add_argument("--topic",
                        help="Topic to produce/consume (for produce/consume mode)")
    parser.add_argument("--kafka",
                        default="broker:9092",
                        help="Kafka cluster (for produce/consume mode)")

    args = parser.parse_args()

    if args.mode == "produce":
        produce_message(args.topic, args.message, args.kafka)
    elif args.mode == "consume":
        consume_messages(args.topic, args.kafka)


if __name__ == "__main__":
    main()
