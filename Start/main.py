import argparse
from kafka import KafkaProducer, KafkaConsumer
import time


def produce_message(topic, message):
    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    future = producer.send(topic, value=message)
    result = future.get(timeout=60)
    print(f"Message sent successfully. Result: {result}")


def consume_messages(topic):
    consumer = KafkaConsumer(
            topic,
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='earliest',
            group_id='my-group'
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
    parser.add_argument("--topic", required=True)
    parser.add_argument("--kafka", default="localhost:9092")

    args = parser.parse_args()

    if args.mode == "produce":
        produce_message(args.topic, args.kafka)
    elif args.mode == "consume":
        consume_messages(args.topic)


if __name__ == "__main__":
    main()
