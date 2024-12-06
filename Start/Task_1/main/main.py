import argparse
import time

from kafka import KafkaConsumer, KafkaProducer


def produce_message(topic, message, kafka_instance):
    producer = KafkaProducer(
            bootstrap_servers=kafka_instance,
            api_version=(0, 10, 1)
    )

    if type(topic) == bytes:
        topic = topic.decode('utf-8')

    future = producer.send(topic, message)
    # result = future.get(timeout=120)
    print(f"Message sent successfully. Result: {future}")


def consume_messages(topic, kafka_instance):
    consumer = KafkaConsumer(
            topic,
            bootstrap_servers=kafka_instance,
            auto_offset_reset='earliest',
            group_id='my-group',
            api_version=(0, 10, 1),
    )

    consumer.subscribe([topic])

    try:
        while True:
            for message in consumer:
                print(f"Received message: {message.value.decode('utf-8')}")
                time.sleep(1)
    except KeyboardInterrupt:
        consumer.close()


def main():
    parser = argparse.ArgumentParser(description="Kafka producer/consumer tool")
    parser.add_argument("--mode", choices=["produce", "consume"], required=True)
    parser.add_argument("--message", help="Message to produce (for produce mode)")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--kafka", default="localhost:9092")

    args = parser.parse_args()

    if args.mode == "produce":
        produce_message(args.topic, args.message, args.kafka)
    elif args.mode == "consume":
        consume_messages(args.topic, args.kafka)


if __name__ == "__main__":
    main()
