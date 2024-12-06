Задание
Вам предстоит написать python-скрипт, который будет взаимодействовать с Apache
Kafka следующим образом: 
1. При исполнении команды
python3 main.py produce --message 'Hello World!' --topic 'hello_topic'
--kafka 'ip:port' Скрипт должен класть сообщение, указанное в параметре message
в топик, указанный в параметре topic, в указанный инстанс Kafka.
2. При исполнении команды:
   python3 main.py consume --topic 'hello_topic' --kafka 'ip:port' Скрипт
   должен подписаться на топик, указанный в параметре 'topic' и в бесконечном
   цикле выводить полученные сообщения.
3. Полученный скрипт нужно упаковать в docker образ. В качестве entrypoint
   указать скрипт.
4. Написать docker-compose файл, с помощью которого будут разворачиваться
   Apache Kafka 

Pure commands:
python3 main.py --mode "produce" --message "Hello World!" --topic "hello_topic" --kafka "0.0.0.0:9092"
python3 main.py --mode "consume" --topic "hello_topic" --kafka "0.0.0.0:9092"
